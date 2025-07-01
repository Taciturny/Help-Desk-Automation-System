"""
Unit tests for KnowledgeRetriever
"""

import json
import sys
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch

# Mock pysqlite3 and other dependencies BEFORE any imports
mock_pysqlite3 = Mock()
sys.modules["pysqlite3"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["cohere"] = MagicMock()

from data_models import RetrievalResult
from retrieval import KnowledgeRetriever


class TestKnowledgeRetriever(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with mocked dependencies."""
        self.mock_cohere_key = "test-api-key"

        # Setup mock cohere client
        self.mock_cohere = MagicMock()
        self.mock_embed_response = MagicMock()
        self.mock_embed_response.embeddings = [[0.1] * 1024]  # 1024-dim embedding
        self.mock_cohere.embed.return_value = self.mock_embed_response

        # Setup mock chromadb collection
        self.mock_collection = MagicMock()
        self.mock_collection.count.return_value = 10
        self.mock_collection.query.return_value = {
            "documents": [["Test document content about password reset"]],
            "metadatas": [
                [{"source": "test_source", "type": "test", "category": "password"}]
            ],
            "distances": [[0.1]],
        }

        # Setup mock chromadb client
        self.mock_chroma_client = MagicMock()
        self.mock_chroma_client.get_collection.side_effect = Exception("Not found")
        self.mock_chroma_client.create_collection.return_value = self.mock_collection

        # Patch all dependencies
        self.patcher1 = patch("retrieval.cohere.Client", return_value=self.mock_cohere)
        self.patcher2 = patch(
            "retrieval.chromadb.PersistentClient", return_value=self.mock_chroma_client
        )
        self.patcher3 = patch("retrieval.Settings", return_value=MagicMock())
        self.patcher4 = patch("os.makedirs")

        self.mock_cohere_client = self.patcher1.start()
        self.mock_chroma = self.patcher2.start()
        self.mock_settings = self.patcher3.start()
        self.mock_makedirs = self.patcher4.start()

        self.retriever = KnowledgeRetriever(self.mock_cohere_key)
        self.retriever.collection = self.mock_collection

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()

    def test_initialization(self):
        """Test proper initialization of KnowledgeRetriever."""
        self.assertEqual(self.retriever.collection_name, "helpdesk_kb")
        self.assertIsNotNone(self.retriever.keyword_categories)
        self.assertIn("password", self.retriever.keyword_categories)

    def test_get_embeddings(self):
        """Test embedding generation."""
        texts = ["test document"]
        embeddings = self.retriever._get_embeddings(texts)
        self.mock_cohere.embed.assert_called_once()
        self.assertEqual(len(embeddings), 1)

    def test_get_embeddings_fallback(self):
        """Test embedding fallback on error."""
        self.mock_cohere.embed.side_effect = [
            Exception("API Error"),
            self.mock_embed_response,
        ]
        _ = self.retriever._get_embeddings(["test"])
        self.assertEqual(self.mock_cohere.embed.call_count, 2)

    def test_query_expansion(self):
        """Test query expansion with related keywords."""
        query = "password problem"
        expanded = self.retriever._expand_query(query)
        self.assertIn("password", expanded)
        self.assertGreater(len(expanded), len(query))

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        distances = [0.1, 0.5, 0.9]
        query = "password reset"
        documents = ["password reset instructions", "general help", "unrelated content"]
        confidences = self.retriever._calculate_confidence(distances, query, documents)
        self.assertEqual(len(confidences), 3)
        self.assertGreater(confidences[0], confidences[1])

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_load_knowledge_base(self, mock_open, mock_exists):
        """Test knowledge base loading."""
        mock_open.return_value.read.return_value = json.dumps(
            {
                "software_guides": {
                    "test": {
                        "title": "Test",
                        "steps": ["Step 1"],
                        "requirements": "None",
                    }
                }
            }
        )

        with patch.object(self.retriever, "_add_to_db") as mock_add:
            count = self.retriever.load_knowledge_base()
            self.assertGreater(count, 0)
            mock_add.assert_called()

    def test_search_knowledge(self):
        """Test knowledge search functionality."""
        results = self.retriever.search_knowledge("test")
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], RetrievalResult)

    def test_search_knowledge_empty_results(self):
        """Test search with no results."""
        self.mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        results = self.retriever.search_knowledge("test")
        self.assertEqual(len(results), 0)

    def test_search_knowledge_error_handling(self):
        """Test search error handling."""
        self.mock_collection.query.side_effect = Exception("Error")
        results = self.retriever.search_knowledge("test")
        self.assertEqual(len(results), 0)

    def test_get_stats(self):
        """Test statistics retrieval."""
        stats = self.retriever.get_stats()
        self.assertEqual(stats["document_count"], 10)
        self.assertEqual(stats["status"], "healthy")

    def test_get_stats_error_handling(self):
        """Test stats error handling."""
        self.mock_collection.count.side_effect = Exception("Error")
        stats = self.retriever.get_stats()
        self.assertEqual(stats["status"], "error")

    def test_process_installation_guides(self):
        """Test installation guide processing."""
        test_data = {
            "software_guides": {
                "test": {"title": "Test", "steps": ["Step 1"], "requirements": "None"}
            }
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            docs = self.retriever._process_installation_guides("test.json")
            self.assertGreater(len(docs), 0)
            self.assertEqual(docs[0]["type"], "installation")

    def test_process_troubleshooting(self):
        """Test troubleshooting guide processing."""
        test_data = {
            "troubleshooting_steps": {"test": {"category": "test", "steps": ["Step 1"]}}
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            docs = self.retriever._process_troubleshooting("test.json")
            self.assertGreater(len(docs), 0)
            self.assertEqual(docs[0]["type"], "troubleshooting")

    def test_add_to_db_batch_processing(self):
        """Test batch processing in _add_to_db."""
        docs = [
            {"content": f"doc{i}", "source": "src", "type": "t", "category": "c"}
            for i in range(15)
        ]
        self.retriever._add_to_db(docs)
        self.assertGreater(self.mock_collection.add.call_count, 1)


if __name__ == "__main__":
    unittest.main()
