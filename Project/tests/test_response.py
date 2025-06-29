from unittest.mock import MagicMock, patch

import pytest

from data_models import RetrievalResult
from response import ResponseGenerator


class TestResponseGenerator:
    @pytest.fixture
    def generator(self):
        with patch("cohere.Client") as mock_cohere:
            generator = ResponseGenerator("test-api-key")
            generator.cohere_client = mock_cohere
            return generator

    def test_empty_context_response(self, generator):
        response = generator.generate_response("test query", [])
        assert "don't have enough information" in response

    @patch.object(ResponseGenerator, "_enhance_prompt_with_context")
    def test_response_generation(self, mock_enhance, generator):
        mock_enhance.return_value = "enhanced prompt"
        mock_response = MagicMock()
        mock_response.generations = [MagicMock(text="generated response")]
        generator.cohere_client.generate.return_value = mock_response

        context = [RetrievalResult(content="test", source="test", relevance_score=0.8)]
        response = generator.generate_response("test query", context)

        assert response == "generated response"
        generator.cohere_client.generate.assert_called_once()

    def test_confidence_calculation(self, generator):
        context = [
            RetrievalResult(content="test", source="test", relevance_score=0.8),
            RetrievalResult(content="test2", source="test2", relevance_score=0.7),
        ]

        # Test with quality indicators
        good_response = "First, follow these steps: 1. Step one. 2. Step two. See more at example.com"
        bad_response = "I'm not sure"

        good_confidence = generator._calculate_response_confidence(
            "query", context, good_response
        )
        bad_confidence = generator._calculate_response_confidence(
            "query", context, bad_response
        )

        assert good_confidence > bad_confidence
        assert good_confidence >= 0.7
