from unittest.mock import MagicMock, patch

import pytest

from data_models import RetrievalResult
from retrieval import KnowledgeRetriever


class TestKnowledgeRetriever:
    @pytest.fixture
    def retriever(self):
        with patch("cohere.Client"), patch("chromadb.Client"):
            retriever = KnowledgeRetriever("test-api-key")
            retriever.collection = MagicMock()
            return retriever

    def test_query_expansion(self, retriever):
        test_cases = [
            ("password reset", ["password", "login", "authenticate"]),
            ("wifi problem", ["wifi", "network", "connection"]),
            ("install software", ["install", "software", "app"]),
        ]

        for query, expected_keywords in test_cases:
            expanded = retriever._expand_query(query)
            expanded_lower = expanded.lower()
            # Check that at least 2 of the expected keywords are present
            assert (
                sum(kw in expanded_lower for kw in expected_keywords) >= 2
            ), f"Expected at least 2 of {expected_keywords} in expanded query '{expanded}'"

    def test_search_knowledge(self, retriever):
        # Mock ChromaDB response
        mock_results = {
            "documents": [["test document content"]],
            "metadatas": [[{"source": "test_source", "type": "test_type"}]],
            "distances": [[0.5]],
        }
        retriever.collection.query.return_value = mock_results

        results = retriever.search_knowledge("test query")
        assert len(results) == 1
        assert isinstance(results[0], RetrievalResult)
        assert results[0].content == "test document content"
        assert 0 < results[0].relevance_score < 1.0

    def test_empty_search(self, retriever):
        retriever.collection.query.return_value = {"documents": [[]]}
        results = retriever.search_knowledge("nonexistent query")
        assert len(results) == 0
