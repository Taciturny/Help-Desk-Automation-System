from unittest.mock import MagicMock, patch

import pytest

from classifier import RequestClassifier
from data_models import RequestCategory
from escalation import EscalationEngine
from response import ResponseGenerator
from retrieval import KnowledgeRetriever


class TestFullWorkflow:
    @pytest.fixture
    def mock_system(self):
        with patch('cohere.Client'), patch('chromadb.Client'):
            classifier = RequestClassifier()
            engine = EscalationEngine()
            retriever = KnowledgeRetriever("test-api-key")
            generator = ResponseGenerator("test-api-key", retriever)

            # Mock the retriever
            retriever.search_knowledge = MagicMock(
                return_value=[
                    MagicMock(
                        content="test content", source="test", relevance_score=0.8
                    )
                ]
            )

            # Mock the response generator
            generator.cohere_client.generate.return_value = MagicMock(
                generations=[MagicMock(text="generated response")]
            )

            return {
                "classifier": classifier,
                "engine": engine,
                "retriever": retriever,
                "generator": generator,
            }

    def test_password_reset_workflow(self, mock_system):
        request = "I forgot my password and need to reset it"

        # Step 1: Classification
        classification = mock_system["classifier"].classify_request(request)
        assert classification.category == RequestCategory.PASSWORD_RESET

        # Step 2: Knowledge Retrieval
        docs = mock_system["retriever"].search_knowledge(request)
        assert len(docs) > 0

        # Step 3: Response Generation
        response = mock_system["generator"].generate_response(request, docs)
        assert "generated response" in response

        # Step 4: Escalation Decision
        ticket_data = {
            "description": request,
            "category": classification.category.value,
            "classification_confidence": classification.confidence,
        }
        escalation = mock_system["engine"].get_escalation_recommendation(ticket_data)

        # Password reset shouldn't escalate by default
        assert escalation["should_escalate"] is False
