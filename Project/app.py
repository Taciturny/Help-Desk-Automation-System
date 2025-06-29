"""
IT Help Desk System - Flask API
===============================
Optimized REST API integrating classification, escalation, and knowledge retrieval.
"""

import logging
import os
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Import your existing modules
from classifier  import RequestClassifier
from escalation import EscalationEngine
from response import ResponseGenerator
from retrieval import KnowledgeRetriever

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config["JSON_SORT_KEYS"] = False


class HelpDeskAPI:
    """Unified Help Desk API handler."""

    def __init__(self):
        self.classifier = RequestClassifier()
        self.escalation_engine = EscalationEngine()

        # Initialize retrieval system if API key is available
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.knowledge_enabled = False

        if self.cohere_api_key and self.cohere_api_key.strip() and self.cohere_api_key != "your-api-key-here":
            try:
                # Test the API key first with a simple request
                import cohere
                co = cohere.Client(self.cohere_api_key)
                # Test with a simple embedding
                test_response = co.embed(texts=["test"], model="embed-english-v3.0")

                # If test passes, initialize the full system
                self.retriever = KnowledgeRetriever(self.cohere_api_key)
                self.response_generator = ResponseGenerator(
                    self.cohere_api_key, self.retriever
                )
                self.knowledge_enabled = True

                # Load knowledge base on startup
                try:
                    doc_count = self.retriever.load_knowledge_base()
                    logger.info(f"Knowledge base loaded with {doc_count} documents")
                except Exception as kb_error:
                    logger.error(f"Failed to load knowledge base: {kb_error}")
                    # Keep knowledge system enabled but with empty KB

            except Exception as e:
                logger.error(f"Failed to initialize knowledge system: {e}")
                logger.warning("Running without knowledge features")
                self.knowledge_enabled = False
        else:
            logger.warning("COHERE_API_KEY not set or invalid - knowledge features disabled")

    def process_request(
        self, user_request: str, user_info: Dict = None
    ) -> Dict[str, Any]:
        """Process complete help desk request with all components."""

        try:
            # Step 1: Classify the request
            classification = self.classifier.classify_request(user_request)

            # Step 2: Build ticket data for escalation
            ticket_data = {
                "description": user_request,
                "category": classification.category.value,
                "classification_confidence": classification.confidence,
                "user_message": user_request,
            }

            # Add user info if provided
            if user_info:
                ticket_data.update(user_info)

            # Step 3: Check escalation
            escalation = self.escalation_engine.get_escalation_recommendation(ticket_data)

            # Step 4: Generate knowledge-based response if available
            knowledge_response = None
            if self.knowledge_enabled and classification.confidence > 0.3:
                try:
                    # Choose template based on category
                    template_map = {
                        "hardware_failure": "troubleshooting",
                        "software_installation": "installation",
                        "policy_question": "policy",
                    }
                    template = template_map.get(classification.category.value, "standard")

                    knowledge_response = self.response_generator.get_knowledge_response(
                        user_request, template
                    )
                except Exception as e:
                    logger.error(f"Knowledge response error: {e}")
                    # Continue without knowledge response

            # Step 5: Compile final response
            return {
                "request_id": f"REQ-{hash(user_request) % 100000:05d}",
                "classification": {
                    "category": classification.category.value,
                    "confidence": round(classification.confidence, 3),
                    "keywords_matched": classification.keywords_matched,
                    "reasoning": classification.reasoning,
                },
                "escalation": escalation,
                "knowledge_response": (
                    {
                        "available": self.knowledge_enabled,
                        "answer": knowledge_response.answer if knowledge_response else None,
                        "confidence": (
                            round(knowledge_response.confidence, 3)
                            if knowledge_response
                            else 0
                        ),
                        "sources_count": (
                            len(knowledge_response.relevant_documents)
                            if knowledge_response
                            else 0
                        ),
                    }
                    if self.knowledge_enabled
                    else {"available": False}
                ),
                "recommendation": self._get_recommendation(
                    classification, escalation, knowledge_response
                ),
            }

        except Exception as e:
            logger.error(f"Error in process_request: {e}")
            # Return a basic response if processing fails
            return {
                "request_id": f"REQ-{hash(user_request) % 100000:05d}",
                "classification": {
                    "category": "general_inquiry",
                    "confidence": 0.5,
                    "keywords_matched": [],
                    "reasoning": "Error occurred during classification",
                },
                "escalation": {
                    "should_escalate": True,
                    "escalation_level": "level_1",
                    "description": "Manual review required due to processing error",
                    "estimated_time": "4 hours"
                },
                "knowledge_response": {"available": False},
                "recommendation": "Your request needs human review due to a system processing error.",
            }

    def _get_recommendation(
        self, classification, escalation, knowledge_response
    ) -> str:
        """Generate user-friendly recommendation."""

        if escalation["should_escalate"]:
            return f"This request should be escalated to {escalation['escalation_level']} - {escalation['description']}"

        if knowledge_response and knowledge_response.confidence > 0.6:
            return "I found relevant information that should help resolve your issue."

        if classification.confidence > 0.7:
            return f"Your request has been classified as {classification.category.value.replace('_', ' ').title()}. Standard resolution procedures will be followed."

        return (
            "Your request needs human review for proper classification and resolution."
        )


# Initialize the API
helpdesk_api = HelpDeskAPI()


# Routes
@app.route("/")
def index():
    """Serve the main interface."""
    return render_template("index.html")


@app.route("/api/health")
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "features": {
                "classification": True,
                "escalation": True,
                "knowledge_retrieval": helpdesk_api.knowledge_enabled,
            },
        }
    )


@app.route("/api/process", methods=["POST"])
def process_request():
    """Process a help desk request."""
    try:
        data = request.get_json()

        if not data or "request" not in data:
            return jsonify({"error": "Missing 'request' field"}), 400

        user_request = data["request"].strip()
        if not user_request:
            return jsonify({"error": "Empty request"}), 400

        # Optional user info
        user_info = data.get("user_info", {})

        # Process the request
        result = helpdesk_api.process_request(user_request, user_info)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e) if app.debug else "Please try again"
        }), 500


@app.route("/api/classify", methods=["POST"])
def classify_only():
    """Classification-only endpoint."""
    try:
        data = request.get_json()
        user_request = data.get("request", "").strip()

        if not user_request:
            return jsonify({"error": "Empty request"}), 400

        classification = helpdesk_api.classifier.classify_request(user_request)

        return jsonify(
            {
                "category": classification.category.value,
                "confidence": round(classification.confidence, 3),
                "keywords_matched": classification.keywords_matched,
                "reasoning": classification.reasoning,
            }
        )

    except Exception as e:
        logger.error(f"Classification error: {e}")
        return jsonify({"error": "Classification failed", "details": str(e)}), 500


@app.route("/api/knowledge", methods=["POST"])
def knowledge_search():
    """Knowledge search endpoint."""
    if not helpdesk_api.knowledge_enabled:
        return jsonify({"error": "Knowledge system not available"}), 503

    try:
        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Empty query"}), 400

        # Search knowledge base
        results = helpdesk_api.retriever.search_knowledge(query, n_results=5)

        return jsonify(
            {
                "query": query,
                "results": [
                    {
                        "content": (
                            result.content[:200] + "..."
                            if len(result.content) > 200
                            else result.content
                        ),
                        "source": result.source,
                        "relevance": round(result.relevance_score, 3),
                        "type": result.metadata.get("type", "unknown"),
                    }
                    for result in results
                ],
            }
        )

    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        return jsonify({"error": "Knowledge search failed", "details": str(e)}), 500


@app.route("/api/stats")
def get_stats():
    """Get system statistics."""
    try:
        stats = {
            "classification_categories": len(helpdesk_api.classifier.category_patterns),
            "escalation_rules": len(helpdesk_api.escalation_engine.rules),
            "knowledge_system": helpdesk_api.knowledge_enabled,
        }

        if helpdesk_api.knowledge_enabled:
            try:
                kb_stats = helpdesk_api.retriever.get_stats()
                stats["knowledge_base"] = kb_stats
            except Exception as e:
                logger.error(f"Error getting KB stats: {e}")
                stats["knowledge_base"] = {"error": "Stats unavailable"}

        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Stats unavailable"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Add this for Render
application = app

# Keep this for local development
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     debug = os.environ.get("DEBUG", "False").lower() == "true"

#     logger.info(f"Starting Help Desk API on port {port}")
#     logger.info(
#         f"Knowledge system: {'Enabled' if helpdesk_api.knowledge_enabled else 'Disabled'}"
#     )

#     app.run(host="0.0.0.0", port=port, debug=debug)

# Add this for Render
# application = app
