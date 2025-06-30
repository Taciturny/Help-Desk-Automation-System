"""
Help Desk Request Classification System - FIXED VERSION
============================================================
Enhanced system for accurately classifying IT support requests and filtering non-IT questions.
"""

import json
import re
from typing import Dict, Set

from data_models import ClassificationResult, RequestCategory


class RequestClassifier:
    """
    Enhanced classifier for IT support requests with better context understanding.
    """

    def __init__(self, categories_file: str = "categories.json"):
        self.categories_data = self._load_categories(categories_file)
        self.category_patterns = self._build_patterns()
        self.non_it_indicators = self._build_non_it_indicators()

    def _load_categories(self, categories_file: str) -> Dict:
        """Load categories from JSON file."""
        try:
            with open(categories_file) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {categories_file} not found. Using default patterns.")
            return {}

    def _build_non_it_indicators(self) -> Set[str]:
        """Build indicators for non-IT questions that should be filtered out."""
        return {
            # Food/dining related
            "cafeteria",
            "menu",
            "food",
            "lunch",
            "dinner",
            "restaurant",
            "eat",
            "dining",
            "kitchen",
            "coffee",
            "tea",
            "snack",
            "meal",
            "breakfast",
            # HR/administrative
            "vacation",
            "holiday",
            "payroll",
            "salary",
            "benefits",
            "hr",
            "human resources",
            "leave",
            "sick day",
            "time off",
            "pto",
            "401k",
            "insurance",
            # Facilities/building
            "parking",
            "elevator",
            "restroom",
            "bathroom",
            "cleaning",
            "temperature",
            "air conditioning",
            "heating",
            "building",
            "office space",
            "desk",
            # Personal/non-work
            "personal",
            "home",
            "family",
            "weather",
            "sports",
            "news",
            "entertainment",
            "shopping",
            "recipe",
            "health",
            "medical",
            "doctor",
            # General questions
            "what time",
            "when is",
            "where is",
            "directions",
            "location",
            "address",
            "phone number",
            "contact",
            "who is",
            "biography",
            # Hypothetical scenarios (like coffee spills)
            "what if",
            "what would happen",
            "suppose",
            "imagine",
            "hypothetical",
            "if i",
            "what happens when",
            "spill",
            "drop",
            "accidentally",
        }

    def _build_patterns(self) -> Dict:
        """Build enhanced keyword patterns for each category."""
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
                    "can't log in",
                    "unable to login",
                    "access denied",
                ],
                "patterns": [
                    r"forgot.*password",
                    r"can't.*log.*in",
                    r"unable.*to.*log",
                    r"reset.*password",
                    r"locked.*out",
                    r"login.*problem",
                    r"password.*expired",
                    r"authentication.*fail",
                ],
                "required_context": [
                    "computer",
                    "system",
                    "account",
                    "work",
                    "login",
                    "access",
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
                    "installer",
                    "setup wizard",
                    "deploy",
                ],
                "patterns": [
                    r"install.*software",
                    r"setup.*application",
                    r"installation.*error",
                    r"can't.*install",
                    r"need.*to.*install",
                    r"how.*to.*install",
                    r"software.*installation",
                ],
                "required_context": [
                    "software",
                    "program",
                    "application",
                    "computer",
                    "work",
                    "laptop",
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
                    "malfunction",
                ],
                "patterns": [
                    r"screen.*flickering",
                    r"laptop.*broken",
                    r"computer.*not.*working",
                    r"hardware.*failure",
                    r"monitor.*black",
                    r"device.*malfunction",
                    r"won't.*turn.*on",
                ],
                "required_context": ["computer", "laptop", "device", "work", "office"],
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
                    "ethernet",
                    "network adapter",
                ],
                "patterns": [
                    r"can't.*connect",
                    r"no.*internet",
                    r"wifi.*problem",
                    r"network.*issue",
                    r"vpn.*not.*working",
                    r"connection.*failed",
                    r"internet.*down",
                ],
                "required_context": [
                    "network",
                    "internet",
                    "wifi",
                    "connection",
                    "work",
                    "office",
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
                    "exchange",
                    "smtp",
                    "imap",
                ],
                "patterns": [
                    r"email.*not.*sync",
                    r"outlook.*problem",
                    r"not.*receiving.*email",
                    r"mail.*configuration",
                    r"distribution.*list",
                    r"email.*setup",
                ],
                "required_context": ["email", "work", "office", "business"],
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
                    "breach",
                    "threat",
                    "attack",
                ],
                "patterns": [
                    r"suspicious.*email",
                    r"think.*hacked",
                    r"security.*incident",
                    r"malware.*infection",
                    r"strange.*pop.*up",
                    r"virus.*detected",
                    r"security.*breach",
                ],
                "required_context": ["computer", "system", "work", "security"],
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
                    "compliance",
                    "regulation",
                    "standard",
                ],
                "patterns": [
                    r"what.*policy",
                    r"company.*policy",
                    r"need.*approval",
                    r"allowed.*to",
                    r"policy.*for",
                    r"compliance.*requirement",
                ],
                "required_context": [
                    "company",
                    "work",
                    "business",
                    "office",
                    "it",
                    "technology",
                ],
            },
        }

    def _is_non_it_request(self, request: str) -> bool:
        """Check if the request is clearly non-IT related."""
        request_lower = request.lower()

        # Check for non-IT indicators
        non_it_matches = sum(
            1 for indicator in self.non_it_indicators if indicator in request_lower
        )

        # Strong non-IT indicators
        if non_it_matches >= 2:
            return True

        # Check for common non-IT patterns
        non_it_patterns = [
            r"cafeteria.*menu",
            r"where.*is.*the.*cafeteria",
            r"what.*time.*does.*cafeteria",
            r"coffee.*spill",
            r"what.*if.*spill",
            r"what.*would.*happen.*if",
            r"parking.*space",
            r"how.*to.*get.*to",
            r"when.*does.*cafeteria",
            r"where.*can.*i.*find.*menu",
        ]

        for pattern in non_it_patterns:
            if re.search(pattern, request_lower):
                return True

        return False

    def _has_it_context(self, request: str, category_patterns: Dict) -> bool:
        """Check if request has sufficient IT context for the category."""
        request_lower = request.lower()
        required_context = category_patterns.get("required_context", [])

        if not required_context:
            return True

        context_matches = sum(
            1 for context in required_context if context in request_lower
        )

        # Need at least one contextual match for IT relevance
        return context_matches > 0

    def classify_request(self, request: str) -> ClassificationResult:
        """
        Enhanced classification with better context understanding and non-IT filtering.
        """
        if not request or not request.strip():
            return ClassificationResult(
                category=RequestCategory.UNKNOWN,
                confidence=0.0,
                keywords_matched=[],
                reasoning="Empty or invalid request",
            )

        # First check if it's a non-IT request
        if self._is_non_it_request(request):
            return ClassificationResult(
                category=RequestCategory.NON_IT_REQUEST,
                confidence=0.0,
                keywords_matched=[],
                reasoning="Non-IT related request - outside scope of IT support",
            )

        request_lower = request.lower()
        category_scores = {}
        all_matched_keywords = {}

        # Score each category based on keyword matches and patterns
        for category, criteria in self.category_patterns.items():
            score = 0
            matched_keywords = []

            # Check if request has IT context for this category
            if not self._has_it_context(request, criteria):
                continue

            # Check keyword matches
            for keyword in criteria["keywords"]:
                if keyword in request_lower:
                    score += 1
                    matched_keywords.append(keyword)

            # Check pattern matches (weighted higher)
            for pattern in criteria["patterns"]:
                if re.search(pattern, request_lower):
                    score += 3  # Increased weight for pattern matches
                    matched_keywords.append(f"pattern: {pattern}")

            if score > 0:
                category_scores[category] = score
                all_matched_keywords[category] = matched_keywords

        # Determine best match
        if not category_scores:
            return ClassificationResult(
                category=RequestCategory.NON_IT_REQUEST,
                confidence=0.0,
                keywords_matched=[],
                reasoning="No matching IT-related keywords or patterns found",
            )

        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]
        matched_keywords = all_matched_keywords.get(best_category, [])

        # Enhanced confidence calculation
        if max_score >= 6:
            confidence = min(0.95, 0.85 + (max_score - 6) * 0.02)
        elif max_score >= 4:
            confidence = 0.75 + (max_score - 4) * 0.05
        elif max_score >= 2:
            confidence = 0.55 + (max_score - 2) * 0.10
        elif max_score == 1:
            confidence = 0.35
        else:
            confidence = 0.1

        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            keywords_matched=all_matched_keywords[best_category],
            reasoning=f"Matched {max_score} IT-related indicators for {best_category.value}",
        )

    def get_category_info(self, category: RequestCategory) -> Dict:
        """Get information about a specific category from categories.json"""
        if self.categories_data and "categories" in self.categories_data:
            return self.categories_data["categories"].get(category.value, {})
        return {}


# Example usage and testing
def main():
    """Test the enhanced classification system."""
    classifier = RequestClassifier()

    test_requests = [
        # IT requests
        "I forgot my password and can't log into my computer. How do I reset it?",
        "I'm trying to install new software but keep getting an error message.",
        "My laptop screen went completely black and won't turn on.",
        "I can connect to WiFi but can't access any websites.",
        "My email stopped syncing yesterday and I'm not receiving messages.",
        "I think someone hacked my computer because I'm seeing strange pop-ups.",
        "What's the policy for installing personal software on work computers?",
        # Non-IT requests (should be filtered out)
        "Where can I find the cafeteria menu?",
        "What would happen if I spilled coffee on my laptop?",
        "What time does the cafeteria open?",
        "Where is the parking garage?",
        "How do I get to the main building?",
        "What's the weather like today?",
        "When is the next company meeting?",
    ]

    print("=== ENHANCED CLASSIFICATION TESTING ===\n")

    for i, request in enumerate(test_requests, 1):
        result = classifier.classify_request(request)

        print(f"Request {i}: {request}")
        print(f"Category: {result.category.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Keywords: {result.keywords_matched}")
        print(f"Reasoning: {result.reasoning}")

        if result.category == RequestCategory.UNKNOWN and result.confidence == 0.0:
            print("✅ Correctly filtered as non-IT request")
        elif result.confidence > 0.7:
            print("✅ High confidence IT classification")
        elif result.confidence > 0.4:
            print("⚠️ Medium confidence classification")
        else:
            print("❌ Low confidence classification")

        print("-" * 80)


if __name__ == "__main__":
    main()
