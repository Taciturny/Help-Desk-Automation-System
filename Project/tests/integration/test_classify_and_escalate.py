import pytest

from classifier import RequestClassifier
from data_models import EscalationLevel, RequestCategory
from escalation import EscalationEngine


class TestClassifyAndEscalate:
    @pytest.fixture
    def classifier(self):
        return RequestClassifier()

    @pytest.fixture
    def engine(self):
        return EscalationEngine()

    def test_security_incident_flow(self, classifier, engine):
        request = "I think my computer has a virus - getting strange popups"

        # Classification
        classification = classifier.classify_request(request)
        assert classification.category == RequestCategory.SECURITY_INCIDENT
        assert classification.confidence > 0.7

        # Escalation
        ticket_data = {
            "description": request,
            "category": classification.category.value,
            "classification_confidence": classification.confidence,
        }
        escalation = engine.get_escalation_recommendation(ticket_data)

        assert escalation["should_escalate"] is True
        assert escalation["escalation_level"] == EscalationLevel.SECURITY_TEAM.value

    def test_low_confidence_flow(self, classifier, engine):
        request = "Something is wrong with my system but I don't know what"

        classification = classifier.classify_request(request)
        assert classification.category == RequestCategory.UNKNOWN
        assert classification.confidence < 0.5

        ticket_data = {
            "description": request,
            "classification_confidence": classification.confidence,
        }
        escalation = engine.get_escalation_recommendation(ticket_data)

        assert escalation["should_escalate"] is True
        assert escalation["escalation_level"] == EscalationLevel.LEVEL_2.value
