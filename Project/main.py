#!/usr/bin/env python3
"""
Interactive Help Desk System - Main Entry Point
===============================================
Integrated system for classifying, retrieving, and responding to IT support requests.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict

# Import system components
from classifier import RequestClassifier
from data_models import RequestCategory, UserRequest
from escalation import EscalationEngine
from response import ResponseGenerator
from retrieval import KnowledgeRetriever


class HelpDeskSystem:
    """Integrated help desk system with all components."""

    def __init__(self, cohere_api_key: str):
        print("🔧 Initializing Help Desk System...")

        try:
            # Initialize components
            self.classifier = RequestClassifier()
            self.escalation_engine = EscalationEngine()
            self.retriever = KnowledgeRetriever(cohere_api_key)
            self.response_generator = ResponseGenerator(cohere_api_key, self.retriever)

            # Load knowledge base
            print("📚 Loading knowledge base...")
            doc_count = self.retriever.load_knowledge_base()
            print(f"✅ Loaded {doc_count} knowledge documents")

            self.is_ready = True
            print("🚀 Help Desk System ready!\n")

        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            self.is_ready = False

    def process_request(
        self, user_message: str, user_email: str = "user@company.com"
    ) -> Dict[str, Any]:
        """Process a complete help desk request."""
        if not self.is_ready:
            return {"error": "System not properly initialized"}

        # Create user request
        user_request = UserRequest(
            id=f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            message=user_message,
            timestamp=datetime.now().isoformat(),
            user_email=user_email,
        )

        # Step 1: Classify the request
        print("🔍 Classifying request...")
        classification = self.classifier.classify_request(user_message)

        # Step 2: Check for escalation
        print("⚡ Checking escalation rules...")
        ticket_data = {
            "category": classification.category.value,
            "classification_confidence": classification.confidence,
            "description": user_message,
            "user_message": user_message,
        }
        escalation_recommendation = (
            self.escalation_engine.get_escalation_recommendation(ticket_data)
        )

        # Step 3: Generate knowledge-based response
        print("🧠 Generating response...")
        template_type = self._get_template_type(classification.category)
        knowledge_response = self.response_generator.get_knowledge_response(
            user_message, template_type
        )

        # Compile final response
        return {
            "request_id": user_request.id,
            "classification": {
                "category": classification.category.value,
                "confidence": classification.confidence,
                "keywords_matched": classification.keywords_matched,
                "reasoning": classification.reasoning,
            },
            "escalation": escalation_recommendation,
            "knowledge_response": {
                "answer": knowledge_response.answer,
                "confidence": knowledge_response.confidence,
                "sources_used": len(knowledge_response.relevant_documents),
            },
            "timestamp": user_request.timestamp,
        }

    def _get_template_type(self, category: RequestCategory) -> str:
        """Map categories to appropriate response templates."""
        template_mapping = {
            RequestCategory.SOFTWARE_INSTALLATION: "installation",
            RequestCategory.HARDWARE_FAILURE: "troubleshooting",
            RequestCategory.NETWORK_CONNECTIVITY: "troubleshooting",
            RequestCategory.POLICY_QUESTION: "policy",
            RequestCategory.SECURITY_INCIDENT: "standard",
        }
        return template_mapping.get(category, "standard")

    def print_response(self, result: Dict[str, Any]):
        """Print formatted response to user."""
        print("\n" + "=" * 60)
        print(f"📋 REQUEST ID: {result['request_id']}")
        print("=" * 60)

        # Classification info
        cls = result["classification"]
        print(f"🏷️  CATEGORY: {cls['category'].replace('_', ' ').title()}")
        print(f"🎯 CONFIDENCE: {cls['confidence']:.2f}")

        # Escalation status
        esc = result["escalation"]
        if esc["should_escalate"]:
            print(f"⚠️  ESCALATION: {esc['escalation_level']} ({esc['priority']})")
            print(f"📞 CONTACT: {esc['contact_info']}")
        else:
            print("✅ NO ESCALATION NEEDED")

        # Knowledge response
        kr = result["knowledge_response"]
        print(f"\n💡 RESPONSE (Confidence: {kr['confidence']:.2f}):")
        print("-" * 40)
        print(kr["answer"])
        print(f"\n📖 Sources used: {kr['sources_used']}")


def interactive_mode():
    """Run the system in interactive mode."""
    print("🎯 INTELLIGENT HELP DESK SYSTEM")
    print("=" * 50)

    # Check for API key
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("❌ Error: COHERE_API_KEY environment variable not set")
        print("Please set your Cohere API key: export COHERE_API_KEY='your-key-here'")
        sys.exit(1)

    # Initialize system
    system = HelpDeskSystem(api_key)
    if not system.is_ready:
        print("❌ System failed to initialize. Exiting.")
        sys.exit(1)

    print("Type 'quit' or 'exit' to end the session")
    print("Type 'demo' to run demonstration queries")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n💬 Enter your IT support request: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Thank you for using the Help Desk System!")
                break

            if user_input.lower() == "demo":
                run_demo(system)
                continue

            if not user_input:
                print("⚠️  Please enter a request.")
                continue

            # Process the request
            result = system.process_request(user_input)

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            # Display the response
            system.print_response(result)

        except KeyboardInterrupt:
            print("\n\n👋 Session ended by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def run_demo(system: HelpDeskSystem):
    """Run demonstration with sample queries."""
    demo_queries = [
        "I forgot my password and can't log into my computer",
        "My WiFi connection keeps dropping every few minutes",
        "How do I install Slack on my work laptop?",
        "I think my computer has been hacked - seeing strange pop-ups",
        "What's the company policy on using personal cloud storage?",
        "I've lost 3 days of work and my boss will fire me if I don't fix this now!!!",
        "Where can I find the cafeteria menu?",
    ]

    print("\n🎭 RUNNING DEMONSTRATION")
    print("=" * 40)

    for i, query in enumerate(demo_queries, 1):
        print(f"\n📝 Demo Query {i}: {query}")
        result = system.process_request(query)

        if "error" not in result:
            # Simplified demo output
            cls = result["classification"]
            esc = result["escalation"]
            kr = result["knowledge_response"]

            print(f"   Category: {cls['category']} (conf: {cls['confidence']:.2f})")
            print(f"   Escalate: {'Yes' if esc['should_escalate'] else 'No'}")
            print(f"   Response confidence: {kr['confidence']:.2f}")
            print(f"   Answer preview: {kr['answer'][:100]}...")
        else:
            print(f"   Error: {result['error']}")

    print("\n🎭 Demo completed!")


def batch_mode(queries_file: str):
    """Process queries from file in batch mode."""
    if not os.path.exists(queries_file):
        print(f"❌ File not found: {queries_file}")
        return

    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("❌ COHERE_API_KEY environment variable not set")
        return

    system = HelpDeskSystem(api_key)
    if not system.is_ready:
        return

    print(f"📂 Processing queries from {queries_file}")

    with open(queries_file) as f:
        queries = [line.strip() for line in f if line.strip()]

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}/{len(queries)} ---")
        result = system.process_request(query)
        system.print_response(result)


def main():
    """Main entry point with command line argument handling."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch" and len(sys.argv) > 2:
            batch_mode(sys.argv[2])
        elif sys.argv[1] in ["--help", "-h"]:
            print("Usage:")
            print("  python main.py                 # Interactive mode")
            print("  python main.py --batch <file>  # Batch mode")
            print("  python main.py --help          # Show this help")
        else:
            print("❌ Invalid arguments. Use --help for usage information.")
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
