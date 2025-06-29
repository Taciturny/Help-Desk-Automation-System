import pytest

from data_models import EscalationLevel, EscalationPriority
from escalation import EscalationEngine


class TestEscalationEngine:
    @pytest.fixture
    def engine(self):
        return EscalationEngine()

    def test_security_incident(self, engine):
        ticket = {
            "title": "Security alert",
            "description": "Possible malware infection detected",
            "category": "security_incident",
            "classification_confidence": 0.9,
        }

        recommendation = engine.get_escalation_recommendation(ticket)
        assert recommendation["should_escalate"] is True
        assert recommendation["escalation_level"] == EscalationLevel.SECURITY_TEAM.value
        assert recommendation["priority"] == EscalationPriority.HIGH.value

    def test_low_confidence(self, engine):
        ticket = {
            "title": "Weird computer issue",
            "description": "Something is wrong but I don't know what",
            "classification_confidence": 0.2,
        }

        recommendation = engine.get_escalation_recommendation(ticket)
        assert recommendation["should_escalate"] is True
        assert recommendation["escalation_level"] == EscalationLevel.LEVEL_2.value

    def test_no_escalation(self, engine):
        ticket = {
            "title": "Standard software question",
            "description": "How do I use Excel?",
            "category": "software_question",
            "classification_confidence": 0.8,
        }

        recommendation = engine.get_escalation_recommendation(ticket)
        assert recommendation["should_escalate"] is False

    def test_vip_escalation(self, engine):
        ticket = {
            "title": "CEO laptop issue",
            "description": "The CEO's laptop won't turn on",
            "keywords": ["ceo", "laptop"],
        }

        recommendation = engine.get_escalation_recommendation(ticket)
        assert recommendation["should_escalate"] is True
        assert recommendation["escalation_level"] == EscalationLevel.LEVEL_3.value
        assert "vip-support" in recommendation["contact_info"]
