"""
Unit tests for ResponseGenerator - Optimized and focused
"""

import sys
from unittest.mock import MagicMock, patch

# Mock pysqlite3 and other dependencies BEFORE any imports
sys.modules["pysqlite3"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["cohere"] = MagicMock()

import pytest

from data_models import KnowledgeResponse, RetrievalResult
from response import ResponseGenerator


class TestResponseGenerator:
    """Optimized unit tests for ResponseGenerator."""

    @pytest.fixture
    def mock_cohere_client(self):
        """Mock Cohere client with realistic response."""
        mock_client = MagicMock()
        mock_generation = MagicMock()
        mock_generation.text = "Test response from Cohere"
        mock_client.generate.return_value.generations = [mock_generation]
        return mock_client

    @pytest.fixture
    def mock_retriever(self):
        """Mock retriever with sample documents."""
        retriever = MagicMock()
        retriever.search_knowledge.return_value = [
            RetrievalResult(
                content="Password reset instructions: Go to portal and click reset",
                source="password_guide.md",
                relevance_score=0.8,
                metadata={"type": "guide"},
            ),
            RetrievalResult(
                content="Contact IT support at help@company.com",
                source="contact_info.md",
                relevance_score=0.6,
                metadata={"type": "contact"},
            ),
        ]
        return retriever

    @pytest.fixture
    def generator(self, mock_cohere_client, mock_retriever):
        """ResponseGenerator instance with mocked dependencies."""
        with patch("response.cohere.Client", return_value=mock_cohere_client):
            gen = ResponseGenerator("test-key", mock_retriever)
            gen.cohere_client = mock_cohere_client
            return gen

    def test_analyze_context_quality(self, generator):
        """Test context quality analysis with realistic data."""
        docs = [
            RetrievalResult(
                content="Content 1",
                source="src1",
                relevance_score=0.9,
                metadata={"type": "guide"},
            ),
            RetrievalResult(
                content="Content 2",
                source="src2",
                relevance_score=0.7,
                metadata={"type": "policy"},
            ),
            RetrievalResult(
                content="Content 3",
                source="src3",
                relevance_score=0.8,
                metadata={"type": "contact"},
            ),
        ]

        quality = generator._analyze_context_quality(docs)

        assert 0.7 <= quality["relevance"] <= 0.9
        assert quality["completeness"] == 1.0  # 3 types / 3 = 1.0
        assert 0 < quality["specificity"] <= 1.0

    def test_analyze_context_quality_empty(self, generator):
        """Test context quality with no documents."""
        quality = generator._analyze_context_quality([])
        assert quality == {"relevance": 0.0, "completeness": 0.0, "specificity": 0.0}

    def test_calculate_response_confidence(self, generator):
        """Test confidence calculation with quality indicators."""
        docs = [
            RetrievalResult(
                content="Step 1: Go to portal www.example.com",
                source="src",
                relevance_score=0.8,
                metadata={},
            )
        ]
        response_text = "Follow these steps: First, contact support if needed"

        confidence = generator._calculate_response_confidence(
            "test query", docs, response_text
        )
        assert 0.5 <= confidence <= 1.0  # Should be high due to quality indicators

    def test_generate_response_success(self, generator, mock_cohere_client):
        """Test successful response generation."""
        docs = [
            RetrievalResult(
                content="Test content",
                source="test.md",
                relevance_score=0.8,
                metadata={"type": "guide"},
            )
        ]
        result = generator.generate_response("test query", docs)
        assert result == "Test response from Cohere"
        mock_cohere_client.generate.assert_called_once()

    def test_generate_response_no_context(self, generator):
        """Test response generation with no context documents."""
        result = generator.generate_response("test query", [])
        assert "don't have enough information" in result

    @patch("response.logger")
    def test_generate_response_error_handling(
        self, mock_logger, generator, mock_cohere_client
    ):
        """Test error handling in response generation."""
        mock_cohere_client.generate.side_effect = Exception("API Error")
        docs = [
            RetrievalResult(
                content="Content", source="src", relevance_score=0.8, metadata={}
            )
        ]
        result = generator.generate_response("test query", docs)
        assert "having trouble generating" in result
        mock_logger.error.assert_called_once()

    def test_get_knowledge_response_relevant_docs(self, generator, mock_retriever):
        """Test knowledge response with relevant documents."""
        mock_retriever.search_knowledge.return_value = [
            RetrievalResult(
                content="Relevant content",
                source="src",
                relevance_score=0.5,
                metadata={"type": "guide"},
            )
        ]
        response = generator.get_knowledge_response("test query")
        assert isinstance(response, KnowledgeResponse)
        assert response.query == "test query"
        assert len(response.relevant_documents) == 1
        assert response.confidence > 0

    def test_get_knowledge_response_no_relevant_docs(self, generator, mock_retriever):
        """Test knowledge response with no relevant documents."""
        mock_retriever.search_knowledge.return_value = [
            RetrievalResult(
                content="Low relevance", source="src", relevance_score=0.2, metadata={}
            )
        ]
        response = generator.get_knowledge_response("test query")
        assert "don't have specific information" in response.answer
        assert len(response.relevant_documents) == 0
        assert response.confidence == 0.0

    def test_get_knowledge_response_no_retriever(self):
        """Test knowledge response without retriever."""
        with patch("response.cohere.Client"):
            generator = ResponseGenerator("test-key")
            with pytest.raises(ValueError, match="Retriever not initialized"):
                generator.get_knowledge_response("test query")

    def test_template_types(self, generator):
        """Test different template types return different prompts."""
        docs = [
            RetrievalResult(
                content="Content",
                source="src",
                relevance_score=0.8,
                metadata={"type": "guide"},
            )
        ]
        standard = generator._enhance_prompt_with_context("query", docs, "standard")
        troubleshooting = generator._enhance_prompt_with_context(
            "query", docs, "troubleshooting"
        )
        assert "expert IT support assistant" in standard
        assert "troubleshooting specialist" in troubleshooting
        assert standard != troubleshooting

    def test_batch_process_success(self, generator):
        """Test successful batch processing."""
        queries = ["query1", "query2"]
        with patch.object(generator, "get_knowledge_response") as mock_get:
            mock_get.return_value = KnowledgeResponse(
                query="test", answer="answer", relevant_documents=[], confidence=0.8
            )
            results = generator.batch_process(queries)
            assert len(results) == 2
            assert mock_get.call_count == 2

    @patch("response.logger")
    def test_batch_process_with_error(self, mock_logger, generator):
        """Test batch processing with one query failing."""
        queries = ["good_query", "bad_query"]
        with patch.object(generator, "get_knowledge_response") as mock_get:
            mock_get.side_effect = [
                KnowledgeResponse("test", "answer", [], 0.8),
                Exception("Test error"),
            ]
            results = generator.batch_process(queries)
            assert len(results) == 2
            assert "Error processing request" in results[1].answer
            mock_logger.error.assert_called_once()


def test_response_integration():
    """Basic integration test without external dependencies."""
    with patch("response.cohere.Client") as mock_cohere:
        mock_client = MagicMock()
        mock_generation = MagicMock()
        mock_generation.text = "Integration test response"
        mock_client.generate.return_value.generations = [mock_generation]
        mock_cohere.return_value = mock_client

        generator = ResponseGenerator("test-key")
        docs = [
            RetrievalResult(
                content="Test content",
                source="test.md",
                relevance_score=0.8,
                metadata={"type": "guide"},
            )
        ]

        result = generator.generate_response("test query", docs)
        assert result == "Integration test response"
