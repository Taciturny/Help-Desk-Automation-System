"""
Unit tests for RequestClassifier
"""

import json
import unittest
from unittest.mock import mock_open, patch

from classifier import RequestClassifier
from data_models import RequestCategory


class TestRequestClassifier(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Mock categories data
        self.mock_categories = {
            "categories": {
                "password_reset": {
                    "description": "Password and login issues",
                    "typical_resolution_time": "15 minutes",
                }
            }
        }

        # Create classifier with mocked file loading
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.mock_categories))
        ):
            self.classifier = RequestClassifier()

    def test_password_reset_classification(self):
        """Test password reset requests."""
        test_cases = [
            "I forgot my password and can't log into my computer",
            "Reset my login credentials please for my work account",
            "Account locked out, need help with computer access",
        ]

        for request in test_cases:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.PASSWORD_RESET)
                self.assertGreater(result.confidence, 0.5)

    def test_software_installation_classification(self):
        """Test software installation requests."""
        test_cases = [
            "I need to install new software on my laptop",
            "How do I setup this application on my computer?",
            "Installation error when downloading program for work",
        ]

        for request in test_cases:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.SOFTWARE_INSTALLATION)
                self.assertGreater(result.confidence, 0.5)

    def test_hardware_failure_classification(self):
        """Test hardware failure requests."""
        test_cases = [
            "My work laptop screen is flickering and won't display properly",
            "Office computer won't turn on this morning",
            "Work keyboard stopped working suddenly on my computer",
        ]

        for request in test_cases:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.HARDWARE_FAILURE)
                self.assertGreater(result.confidence, 0.5)

    def test_network_connectivity_classification(self):
        """Test network connectivity requests."""
        test_cases = [
            "Can't connect to office WiFi network",
            "Internet connection keeps dropping on my work computer",
            "VPN not working from home office",
        ]

        for request in test_cases:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.NETWORK_CONNECTIVITY)
                self.assertGreater(result.confidence, 0.5)

    def test_non_it_request_filtering(self):
        """Test that non-IT requests are properly filtered."""
        non_it_requests = [
            "Where can I find the cafeteria menu?",
            "What time does the cafeteria open?",
            "What would happen if I spilled coffee on my laptop?",
            "Where is the parking garage located?",
            "When is the next company meeting?",
        ]

        for request in non_it_requests:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.NON_IT_REQUEST)
                self.assertEqual(result.confidence, 0.0)

    def test_empty_request(self):
        """Test handling of empty requests."""
        empty_requests = ["", "   ", None]

        for request in empty_requests:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.UNKNOWN)
                self.assertEqual(result.confidence, 0.0)

    def test_confidence_scoring(self):
        """Test confidence scoring logic."""
        # High confidence request (multiple keywords + pattern match + IT context)
        high_conf_request = (
            "I forgot my password and can't log into my work computer account"
        )
        result = self.classifier.classify_request(high_conf_request)
        self.assertGreater(result.confidence, 0.7)

        # Medium confidence request with IT context
        med_conf_request = "need password help for my computer login"
        result = self.classifier.classify_request(med_conf_request)
        self.assertGreater(result.confidence, 0.3)
        self.assertLess(result.confidence, 0.7)

    def test_it_context_requirement(self):
        """Test that IT context is required for classification."""
        # Request with IT keywords but no context - should be filtered as non-IT
        no_context_request = "password for my gym membership"
        result = self.classifier.classify_request(no_context_request)
        self.assertEqual(result.category, RequestCategory.NON_IT_REQUEST)

    def test_pattern_matching(self):
        """Test regex pattern matching."""
        pattern_requests = [
            "can't log in to work system",
            "unable to login to my computer today",
            "login problem with office computer",
        ]

        for request in pattern_requests:
            with self.subTest(request=request):
                result = self.classifier.classify_request(request)
                self.assertEqual(result.category, RequestCategory.PASSWORD_RESET)
                # Pattern matches should boost confidence
                self.assertGreater(result.confidence, 0.6)

    def test_keyword_matching(self):
        """Test that matched keywords are properly recorded."""
        request = "I need to reset my password for computer login"
        result = self.classifier.classify_request(request)

        # Should have matched several keywords
        self.assertGreater(len(result.keywords_matched), 2)
        self.assertIn("password", str(result.keywords_matched).lower())
        self.assertIn("reset", str(result.keywords_matched).lower())

    def test_get_category_info(self):
        """Test category information retrieval."""
        info = self.classifier.get_category_info(RequestCategory.PASSWORD_RESET)
        self.assertIsInstance(info, dict)

    def test_file_not_found_handling(self):
        """Test handling when categories file is not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            classifier = RequestClassifier("nonexistent.json")
            # Should still work with default patterns, but needs IT context
            result = classifier.classify_request(
                "I forgot my password for my work computer"
            )
            self.assertEqual(result.category, RequestCategory.PASSWORD_RESET)


if __name__ == "__main__":
    unittest.main()
