"""
Help Desk Request Classification System - Streamlined Version
============================================================
A focused system for classifying IT support requests.
"""

import json
import re
from typing import Dict, List

from data_models import ClassificationResult, RequestCategory


class RequestClassifier:
    """
    Main classifier for IT support requests using keyword-based classification.
    """

    def __init__(self, categories_file: str = "categories.json"):
        self.categories_data = self._load_categories(categories_file)
        self.category_patterns = self._build_patterns()

    def _load_categories(self, categories_file: str) -> Dict:
        """Load categories from JSON file."""
        try:
            with open(categories_file) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {categories_file} not found. Using default patterns.")
            return {}

    def _build_patterns(self) -> Dict:
        """Build keyword patterns for each category."""
        return {
            RequestCategory.PASSWORD_RESET: {
                "keywords": [
                    "password",
                    "login",
                    "forgot",
                    "reset",
                    "unlock",
                    "locked out",
                    "account locked",
                    "sign in",
                    "authentication",
                    "credentials",
                ],
                "patterns": [
                    r"forgot.*password",
                    r"can't.*log.*in",
                    r"reset.*password",
                    r"locked.*out",
                    r"login.*problem",
                ],
            },
            RequestCategory.SOFTWARE_INSTALLATION: {
                "keywords": [
                    "install",
                    "setup",
                    "software",
                    "application",
                    "app",
                    "program",
                    "download",
                    "upgrade",
                    "update",
                    "configure",
                    "installation",
                ],
                "patterns": [
                    r"install.*software",
                    r"setup.*application",
                    r"installation.*error",
                    r"can't.*install",
                    r"need.*install",
                ],
            },
            RequestCategory.HARDWARE_FAILURE: {
                "keywords": [
                    "laptop",
                    "computer",
                    "screen",
                    "monitor",
                    "keyboard",
                    "mouse",
                    "broken",
                    "damaged",
                    "hardware",
                    "device",
                    "flickering",
                    "black screen",
                    "not working",
                    "died",
                    "failed",
                ],
                "patterns": [
                    r"screen.*flickering",
                    r"laptop.*broken",
                    r"computer.*not.*working",
                    r"hardware.*failure",
                    r"monitor.*black",
                ],
            },
            RequestCategory.NETWORK_CONNECTIVITY: {
                "keywords": [
                    "network",
                    "internet",
                    "wifi",
                    "connection",
                    "connectivity",
                    "vpn",
                    "can't connect",
                    "no internet",
                    "offline",
                    "disconnect",
                ],
                "patterns": [
                    r"can't.*connect",
                    r"no.*internet",
                    r"wifi.*problem",
                    r"network.*issue",
                    r"vpn.*not.*working",
                ],
            },
            RequestCategory.EMAIL_CONFIGURATION: {
                "keywords": [
                    "email",
                    "outlook",
                    "mail",
                    "sync",
                    "syncing",
                    "configuration",
                    "distribution list",
                    "mailbox",
                    "messages",
                    "receiving",
                ],
                "patterns": [
                    r"email.*not.*sync",
                    r"outlook.*problem",
                    r"not.*receiving.*email",
                    r"mail.*configuration",
                    r"distribution.*list",
                ],
            },
            RequestCategory.SECURITY_INCIDENT: {
                "keywords": [
                    "security",
                    "virus",
                    "malware",
                    "suspicious",
                    "hacked",
                    "hack",
                    "phishing",
                    "spam",
                    "pop-up",
                    "suspicious email",
                    "incident",
                ],
                "patterns": [
                    r"suspicious.*email",
                    r"think.*hacked",
                    r"security.*incident",
                    r"malware.*infection",
                    r"strange.*pop.*up",
                ],
            },
            RequestCategory.POLICY_QUESTION: {
                "keywords": [
                    "policy",
                    "procedure",
                    "allowed",
                    "permission",
                    "approval",
                    "what's the policy",
                    "company policy",
                    "guidelines",
                    "rules",
                ],
                "patterns": [
                    r"what.*policy",
                    r"company.*policy",
                    r"need.*approval",
                    r"allowed.*to",
                    r"policy.*for",
                ],
            },
        }

    def classify_request(self, request: str) -> ClassificationResult:
        """
        Classify a user request using keyword matching and pattern recognition.

        Args:
            request: The user's request text

        Returns:
            ClassificationResult with classification details
        """
        if not request or not request.strip():
            return ClassificationResult(
                category=RequestCategory.UNKNOWN,
                confidence=0.0,
                keywords_matched=[],
                reasoning="Empty or invalid request",
            )

        request_lower = request.lower()
        category_scores = {}
        all_matched_keywords = {}

        # Score each category based on keyword matches and patterns
        for category, criteria in self.category_patterns.items():
            score = 0
            matched_keywords = []

            # Check keyword matches
            for keyword in criteria["keywords"]:
                if keyword in request_lower:
                    score += 1
                    matched_keywords.append(keyword)

            # Check pattern matches (weighted higher)
            for pattern in criteria["patterns"]:
                if re.search(pattern, request_lower):
                    score += 2
                    matched_keywords.append(f"pattern: {pattern}")

            if score > 0:
                category_scores[category] = score
                all_matched_keywords[category] = matched_keywords

        # Determine best match
        if not category_scores:
            return ClassificationResult(
                category=RequestCategory.UNKNOWN,
                confidence=0.0,
                keywords_matched=[],
                reasoning="No matching IT-related keywords or patterns found",
            )

        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]

        # Calculate confidence based on score
        if max_score >= 5:
            confidence = min(0.90 + (max_score - 5) * 0.02, 0.95)
        elif max_score >= 3:
            confidence = 0.75 + (max_score - 3) * 0.075
        elif max_score == 2:
            confidence = 0.60
        elif max_score == 1:
            confidence = 0.35
        else:
            confidence = 0.1

        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            keywords_matched=all_matched_keywords[best_category],
            reasoning=f"Matched {max_score} indicators for {best_category.value}",
        )

    def get_category_info(self, category: RequestCategory) -> Dict:
        """Get information about a specific category from categories.json"""
        if self.categories_data and "categories" in self.categories_data:
            return self.categories_data["categories"].get(category.value, {})
        return {}


class ClassificationEvaluator:
    """Utility class for evaluating classifier performance against test data."""

    def __init__(self, classifier: RequestClassifier):
        self.classifier = classifier

    def evaluate_test_requests(self, test_file: str = "test_requests.json") -> Dict:
        """
        Evaluate classifier against test requests from file.

        Args:
            test_file: Path to test requests JSON file

        Returns:
            Evaluation metrics and detailed results
        """
        test_data = self._load_test_data(test_file)
        if not test_data:
            return {"error": "No test data found"}

        results = []
        correct_predictions = 0

        for test_case in test_data:
            request = test_case["request"]
            expected = test_case["expected_classification"]

            result = self.classifier.classify_request(request)
            predicted = result.category.value

            is_correct = predicted == expected
            if is_correct:
                correct_predictions += 1

            results.append(
                {
                    "request": request,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": result.confidence,
                    "correct": is_correct,
                    "keywords_matched": result.keywords_matched,
                }
            )

        accuracy = correct_predictions / len(test_data) if test_data else 0

        return {
            "accuracy": accuracy,
            "total_tests": len(test_data),
            "correct_predictions": correct_predictions,
            "detailed_results": results,
        }

    def _load_test_data(self, test_file: str) -> List[Dict]:
        """Load test data from JSON file."""
        try:
            with open(test_file) as f:
                data = json.load(f)
                return data.get("test_requests", [])
        except FileNotFoundError:
            print(f"Warning: {test_file} not found.")
            return []


# Example usage and testing
def main():
    """Example usage of the classification system."""

    # Initialize classifier
    classifier = RequestClassifier()

    # Test with sample requests
    test_requests = [
        "I forgot my password and can't log into my computer. How do I reset it?",
        "I'm trying to install new software but keep getting an error message.",
        "My laptop screen went completely black and won't turn on.",
        "I can connect to WiFi but can't access any websites.",
        "My email stopped syncing yesterday and I'm not receiving messages.",
        "I think someone hacked my computer because I'm seeing strange pop-ups.",
        "What's the policy for installing personal software on work computers?",
        "Where can I find the cafeteria menu?",  # Non-IT request
    ]

    print("=== Help Desk Request Classification Results ===\n")

    for i, request in enumerate(test_requests, 1):
        result = classifier.classify_request(request)

        print(f"Request {i}: {request}")
        print(f"Category: {result.category.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Keywords: {result.keywords_matched}")
        print(f"Reasoning: {result.reasoning}")
        print("-" * 60)

    # Run evaluation if test file exists
    evaluator = ClassificationEvaluator(classifier)
    eval_results = evaluator.evaluate_test_requests()

    if "error" not in eval_results:
        print("\n=== Evaluation Results ===")
        print(f"Accuracy: {eval_results['accuracy']:.2f}")
        print(
            f"Correct: {eval_results['correct_predictions']}/{eval_results['total_tests']}"
        )


if __name__ == "__main__":
    main()
