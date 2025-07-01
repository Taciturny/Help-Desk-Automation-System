"""
Comprehensive Integration Test Suite
===================================
Tests the complete helpdesk system workflow with realistic scenarios.
"""

import json
import tempfile
from typing import Dict, List

import pytest

# Import all components
from classifier import RequestClassifier
from data_models import (
    KnowledgeResponse,
    RequestCategory,
    RetrievalResult,
)
from escalation import EscalationEngine


class MockRetriever:
    """Mock retriever for testing without external dependencies."""

    def __init__(self):
        # Simulated knowledge base responses
        self.mock_responses = {
            "password": [
                RetrievalResult(
                    content="Password Reset: 1. Go to login page 2. Click 'Forgot Password' 3. Enter email 4. Check inbox for reset link",
                    source="password_guide",
                    relevance_score=0.85,
                    metadata={"type": "troubleshooting", "category": "password"},
                )
            ],
            "wifi": [
                RetrievalResult(
                    content="WiFi Troubleshooting: 1. Check WiFi is enabled 2. Restart network adapter 3. Reconnect to network",
                    source="network_guide",
                    relevance_score=0.80,
                    metadata={"type": "troubleshooting", "category": "network"},
                )
            ],
            "security": [
                RetrievalResult(
                    content="Security Incident: Immediately disconnect from network and contact security team at ext. 5555",
                    source="security_policy",
                    relevance_score=0.95,
                    metadata={"type": "policy", "category": "security"},
                )
            ],
        }

    def search_knowledge(self, query: str, n_results: int = 3) -> List[RetrievalResult]:
        query_lower = query.lower()
        for key, results in self.mock_responses.items():
            if key in query_lower:
                return results[:n_results]
        return []


class MockResponseGenerator:
    """Mock response generator for testing."""

    def __init__(self, retriever=None):
        self.retriever = retriever
        self.response_templates = {
            "password": "To reset your password: 1. Visit the login portal 2. Click 'Forgot Password' 3. Follow email instructions. Contact IT if issues persist.",
            "wifi": "For WiFi issues: 1. Check your network settings 2. Restart WiFi adapter 3. Reconnect to corporate network. Escalate if problem continues.",
            "security": "SECURITY ALERT: This appears to be a security incident. Please disconnect immediately and contact the security team at security@company.com or ext. 5555.",
            "default": "I don't have specific guidance for this issue. Please contact IT support for assistance.",
        }

    def get_knowledge_response(
        self, query: str, template_type: str = "standard"
    ) -> KnowledgeResponse:
        if not self.retriever:
            return KnowledgeResponse(
                query=query,
                answer=self.response_templates["default"],
                relevant_documents=[],
                confidence=0.0,
            )

        docs = self.retriever.search_knowledge(query)
        query_lower = query.lower()

        # Determine response based on query content
        if "password" in query_lower or "login" in query_lower:
            response = self.response_templates["password"]
            confidence = 0.85
        elif "wifi" in query_lower or "network" in query_lower:
            response = self.response_templates["wifi"]
            confidence = 0.80
        elif "security" in query_lower or "hack" in query_lower:
            response = self.response_templates["security"]
            confidence = 0.95
        else:
            response = self.response_templates["default"]
            confidence = 0.3

        return KnowledgeResponse(
            query=query, answer=response, relevant_documents=docs, confidence=confidence
        )


class IntegratedHelpdeskSystem:
    """Main system integrating all components."""

    def __init__(self, use_mocks: bool = True):
        self.classifier = RequestClassifier()
        self.escalation_engine = EscalationEngine()

        if use_mocks:
            self.retriever = MockRetriever()
            self.response_generator = MockResponseGenerator(self.retriever)
        else:
            # Would initialize real components here
            self.retriever = None
            self.response_generator = None

    def process_ticket(self, user_request: str, user_info: Dict = None) -> Dict:
        """Process a complete ticket through the entire workflow."""
        # Step 1: Classify the request
        classification = self.classifier.classify_request(user_request)

        # Step 2: Get knowledge-based response
        knowledge_response = None
        if (
            self.response_generator
            and classification.category != RequestCategory.NON_IT_REQUEST
        ):
            knowledge_response = self.response_generator.get_knowledge_response(
                user_request
            )

        # Step 3: Prepare ticket data for escalation analysis
        ticket_data = {
            "title": (
                user_request[:50] + "..." if len(user_request) > 50 else user_request
            ),
            "description": user_request,
            "category": classification.category.value,
            "classification_confidence": classification.confidence,
            "user_info": user_info or {},
            "knowledge_confidence": (
                knowledge_response.confidence if knowledge_response else 0.0
            ),
        }

        # Add keywords to ticket data for escalation evaluation
        if any(
            word in user_request.lower() for word in ["urgent", "critical", "emergency"]
        ):
            ticket_data["priority"] = "critical"

        # Step 4: Evaluate escalation needs
        escalation_recommendation = (
            self.escalation_engine.get_escalation_recommendation(ticket_data)
        )

        # Step 5: Compile final response
        return {
            "classification": {
                "category": classification.category.value,
                "confidence": classification.confidence,
                "keywords_matched": classification.keywords_matched,
                "reasoning": classification.reasoning,
            },
            "knowledge_response": {
                "answer": (
                    knowledge_response.answer
                    if knowledge_response
                    else "No response generated"
                ),
                "confidence": (
                    knowledge_response.confidence if knowledge_response else 0.0
                ),
                "relevant_docs_count": (
                    len(knowledge_response.relevant_documents)
                    if knowledge_response
                    else 0
                ),
            },
            "escalation": escalation_recommendation,
            "final_recommendation": self._get_final_recommendation(
                classification, knowledge_response, escalation_recommendation
            ),
        }

    def _get_final_recommendation(self, classification, knowledge_response, escalation):
        """Determine the final action recommendation."""
        if classification.category == RequestCategory.NON_IT_REQUEST:
            return "REDIRECT: Not an IT request - redirect to appropriate department"

        if escalation["should_escalate"]:
            return f"ESCALATE: {escalation['description']} - Contact: {escalation['contact_info']}"

        if knowledge_response and knowledge_response.confidence > 0.7:
            return "RESOLVE: High-confidence automated response provided"
        elif knowledge_response and knowledge_response.confidence > 0.4:
            return "ASSIST: Medium-confidence response - may need follow-up"
        else:
            return "ESCALATE: Low confidence - human intervention needed"


class TestHelpdeskIntegration:
    """Comprehensive integration tests."""

    @pytest.fixture
    def system(self):
        """Create integrated system for testing."""
        return IntegratedHelpdeskSystem(use_mocks=True)

    @pytest.fixture
    def test_categories_file(self):
        """Create temporary categories file for testing."""
        categories_data = {
            "categories": {
                "password_reset": {
                    "description": "Password and login issues",
                    "typical_resolution_time": "15 minutes",
                },
                "security_incident": {
                    "description": "Security-related incidents",
                    "typical_resolution_time": "Immediate",
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(categories_data, f)
            return f.name

    def test_password_reset_workflow(self, system):
        """Test complete workflow for password reset request."""
        request = "I forgot my password and can't log into my computer"
        result = system.process_ticket(request)

        # Verify classification
        assert result["classification"]["category"] == "password_reset"
        assert result["classification"]["confidence"] > 0.7

        # Verify knowledge response
        assert "password" in result["knowledge_response"]["answer"].lower()
        assert result["knowledge_response"]["confidence"] > 0.7

        # Verify no escalation needed for standard password reset
        assert not result["escalation"]["should_escalate"]

        # Verify final recommendation
        assert "RESOLVE" in result["final_recommendation"]

    def test_security_incident_workflow(self, system):
        """Test complete workflow for security incident."""
        request = "I think my computer has been hacked - seeing strange pop-ups"
        result = system.process_ticket(request)

        # Verify classification
        assert result["classification"]["category"] == "security_incident"
        assert result["classification"]["confidence"] > 0.6

        # Verify escalation triggered
        assert result["escalation"]["should_escalate"]
        assert result["escalation"]["escalation_level"] == "security_team"
        assert result["escalation"]["priority"] == "high"

        # Verify final recommendation includes escalation
        assert "ESCALATE" in result["final_recommendation"]
        assert "security" in result["final_recommendation"].lower()

    def test_non_it_request_workflow(self, system):
        """Test workflow for non-IT requests."""
        request = "Where can I find the cafeteria menu?"
        result = system.process_ticket(request)

        # Verify correctly identified as non-IT
        assert result["classification"]["category"] == "non_it_request"
        assert result["classification"]["confidence"] == 0.0

        # Verify redirect recommendation
        assert "REDIRECT" in result["final_recommendation"]

    def test_low_confidence_escalation(self, system):
        """Test escalation for low-confidence classifications."""
        request = "Something is wrong with my thing"  # Vague request
        result = system.process_ticket(request)

        # Should trigger low confidence escalation
        if result["classification"]["confidence"] < 0.3:
            assert result["escalation"]["should_escalate"]
            assert "low confidence" in result["escalation"][
                "primary_rule"
            ].lower() or result["final_recommendation"].startswith("ESCALATE")

    def test_critical_priority_handling(self, system):
        """Test handling of critical priority requests."""
        request = "URGENT: System is completely down and not working"
        result = system.process_ticket(request)

        # Should trigger escalation due to critical keywords
        assert result["escalation"]["should_escalate"]
        assert result["escalation"]["priority"] in ["critical", "high"]

    def test_component_error_handling(self, system):
        """Test system behavior when components fail."""
        # Test with empty/invalid input
        result = system.process_ticket("")
        assert result["classification"]["category"] == "unknown"
        assert result["final_recommendation"].startswith(("ESCALATE", "REDIRECT"))

        # Test with very long input
        long_request = "Help me " * 100
        result = system.process_ticket(long_request)
        assert result is not None
        assert "classification" in result

    def test_system_performance_benchmark(self, system):
        """Basic performance test for system responsiveness."""
        import time

        test_requests = [
            "Password reset help",
            "Network connection issue",
            "Software installation problem",
        ]

        start_time = time.time()

        for request in test_requests:
            system.process_ticket(request)

        total_time = time.time() - start_time

        # Should process 3 requests in under 1 second with mocks
        assert total_time < 1.0, f"Performance issue: {total_time:.2f}s for 3 requests"


def run_integration_demo():
    """Demonstrate the integrated system with realistic scenarios."""
    print("=== Helpdesk System Integration Demo ===\n")

    system = IntegratedHelpdeskSystem(use_mocks=True)

    demo_scenarios = [
        {
            "request": "I can't log into my work computer, forgot my password",
            "user": {"department": "Marketing", "priority": "normal"},
        },
        {
            "request": "URGENT: I think someone hacked my email account",
            "user": {"department": "Finance", "priority": "critical"},
        },
        {
            "request": "Need to install Slack on my laptop for team communication",
            "user": {"department": "Engineering", "priority": "normal"},
        },
        {
            "request": "What time does the cafeteria open for lunch?",
            "user": {"department": "HR", "priority": "low"},
        },
    ]

    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"--- Scenario {i}: {scenario['user']['department']} User ---")
        print(f"Request: {scenario['request']}")

        result = system.process_ticket(scenario["request"], scenario["user"])

        print(f"Category: {result['classification']['category']}")
        print(f"Confidence: {result['classification']['confidence']:.2f}")
        print(f"Response: {result['knowledge_response']['answer'][:100]}...")
        print(f"Action: {result['final_recommendation']}")
        print()


if __name__ == "__main__":
    # Run the demo
    run_integration_demo()

    # Run tests if pytest is available
    try:
        import pytest

        print("Running integration tests...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Install pytest to run automated tests: pip install pytest")
