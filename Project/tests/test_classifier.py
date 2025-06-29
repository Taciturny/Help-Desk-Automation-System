import pytest

from classifier import RequestClassifier
from data_models import RequestCategory


class TestRequestClassifier:
    @pytest.fixture
    def classifier(self):
        return RequestClassifier()

    def test_empty_request(self, classifier):
        result = classifier.classify_request("")
        assert result.category == RequestCategory.UNKNOWN
        assert result.confidence == 0.0

    def test_password_reset(self, classifier):
        test_cases = [
            ("I forgot my password", ["password", "forgot"]),
            ("Can't login to my account", ["login"]),
            ("Need to reset my credentials", ["reset", "credentials"]),
        ]

        for request, expected_keywords in test_cases:
            result = classifier.classify_request(request)
            assert result.category == RequestCategory.PASSWORD_RESET
            assert all(kw in result.keywords_matched for kw in expected_keywords)
            assert 0.35 <= result.confidence <= 0.95

    def test_hardware_failure(self, classifier):
        request = "My laptop screen is broken and won't turn on"
        result = classifier.classify_request(request)
        assert result.category == RequestCategory.HARDWARE_FAILURE
        assert any(
            kw in result.keywords_matched for kw in ["laptop", "screen", "broken"]
        )
        assert result.confidence > 0.75

    def test_unknown_request(self, classifier):
        request = "Where is the cafeteria?"
        result = classifier.classify_request(request)
        assert result.category == RequestCategory.UNKNOWN
        assert result.confidence == 0.0

    def test_confidence_calculation(self, classifier):
        # Test confidence scaling with multiple matches
        strong_request = (
            "I can't login because I forgot my password and my account is locked"
        )
        weak_request = "Having trouble with login"

        strong_result = classifier.classify_request(strong_request)
        weak_result = classifier.classify_request(weak_request)

        assert strong_result.confidence > weak_result.confidence
        assert strong_result.confidence >= 0.75
