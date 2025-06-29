"""
IT Help Desk System - Streamlit App
===================================
Interactive help desk system with classification, escalation, and knowledge retrieval.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

import streamlit as st

# Import your existing modules
from classifier import RequestClassifier
from escalation import EscalationEngine
from response import ResponseGenerator
from retrieval import KnowledgeRetriever

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="IT Help Desk System",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


class HelpDeskAPI:
    """Unified Help Desk API handler."""

    def __init__(self):
        self.classifier = RequestClassifier()
        self.escalation_engine = EscalationEngine()

        # Initialize retrieval system if API key is available
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.knowledge_enabled = False

        if (
            self.cohere_api_key
            and self.cohere_api_key.strip()
            and self.cohere_api_key != "your-api-key-here"
        ):
            try:
                # Test the API key first with a simple request
                import cohere

                co = cohere.Client(self.cohere_api_key)
                # Test with a simple embedding
                test_response = co.embed(
                    texts=["test"],
                    model="embed-english-v3.0",
                    input_type="search_document",
                )

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

            except Exception as e:
                logger.error(f"Failed to initialize knowledge system: {e}")
                self.knowledge_enabled = False
        else:
            logger.warning(
                "COHERE_API_KEY not set or invalid - knowledge features disabled"
            )

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
            escalation = self.escalation_engine.get_escalation_recommendation(
                ticket_data
            )

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
                    template = template_map.get(
                        classification.category.value, "standard"
                    )

                    knowledge_response = self.response_generator.get_knowledge_response(
                        user_request, template
                    )
                except Exception as e:
                    logger.error(f"Knowledge response error: {e}")

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
                        "answer": (
                            knowledge_response.answer if knowledge_response else None
                        ),
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
                    "estimated_time": "4 hours",
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


# Initialize session state
if 'helpdesk_api' not in st.session_state:
    with st.spinner("Initializing Help Desk System..."):
        st.session_state.helpdesk_api = HelpDeskAPI()

if 'request_history' not in st.session_state:
    st.session_state.request_history = []

# Main UI
st.title("🎧 IT Help Desk System")
st.markdown("---")

# Sidebar with system info
with st.sidebar:
    st.header("System Status")

    # System health check
    health_status = {
        "Classification": "✅ Active",
        "Escalation": "✅ Active",
        "Knowledge Base": (
            "✅ Active"
            if st.session_state.helpdesk_api.knowledge_enabled
            else "❌ Disabled"
        ),
    }

    for feature, status in health_status.items():
        st.write(f"**{feature}:** {status}")

    if not st.session_state.helpdesk_api.knowledge_enabled:
        st.warning(
            "💡 Set COHERE_API_KEY environment variable to enable knowledge features"
        )

    st.markdown("---")

    # Statistics
    st.header("System Stats")
    try:
        stats = {
            "Classification Categories": len(
                st.session_state.helpdesk_api.classifier.category_patterns
            ),
            "Escalation Rules": len(
                st.session_state.helpdesk_api.escalation_engine.rules
            ),
            "Requests Processed": len(st.session_state.request_history),
        }

        if st.session_state.helpdesk_api.knowledge_enabled:
            try:
                kb_stats = st.session_state.helpdesk_api.retriever.get_stats()
                stats["Knowledge Documents"] = kb_stats.get("total_documents", "N/A")
            except:
                stats["Knowledge Documents"] = "Error"

        for stat, value in stats.items():
            st.metric(stat, value)
    except Exception as e:
        st.error(f"Error loading stats: {e}")

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📝 Submit Request",
        "🔍 Classification Only",
        "📚 Knowledge Search",
        "📊 Request History",
    ]
)

with tab1:
    st.header("Submit IT Help Request")

    # User information (optional)
    with st.expander("User Information (Optional)"):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("Name")
            user_department = st.text_input("Department")
        with col2:
            user_email = st.text_input("Email")
            user_priority = st.selectbox(
                "Priority", ["Low", "Medium", "High", "Critical"]
            )

    # Main request input
    st.subheader("Describe Your Issue")
    user_request = st.text_area(
        "Please describe your IT issue in detail:",
        height=150,
        placeholder="Example: My laptop won't turn on after I spilled coffee on it yesterday...",
    )

    # Sample requests for testing
    st.subheader("Quick Test Examples")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🖥️ Hardware Issue"):
            user_request = "My computer screen is flickering and making strange noises"
            st.rerun()

    with col2:
        if st.button("💾 Software Problem"):
            user_request = (
                "I can't install the new Microsoft Office update on my laptop"
            )
            st.rerun()

    with col3:
        if st.button("📋 Policy Question"):
            user_request = (
                "What's the company policy on using personal devices for work?"
            )
            st.rerun()

    # Process request
    if st.button("🚀 Submit Request", type="primary"):
        if user_request.strip():
            with st.spinner("Processing your request..."):
                # Prepare user info
                user_info = {}
                if user_name:
                    user_info["user_name"] = user_name
                if user_department:
                    user_info["department"] = user_department
                if user_email:
                    user_info["email"] = user_email
                if user_priority:
                    user_info["priority"] = user_priority.lower()

                # Process the request
                result = st.session_state.helpdesk_api.process_request(
                    user_request, user_info
                )

                # Add to history
                st.session_state.request_history.append(
                    {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "request": user_request,
                        "result": result,
                    }
                )

                # Display results
                st.success(f"✅ Request processed! ID: {result['request_id']}")

                # Classification results
                st.subheader("🏷️ Classification Results")
                classification = result['classification']

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Category", classification['category'].replace('_', ' ').title()
                    )
                    st.metric("Confidence", f"{classification['confidence']:.1%}")

                with col2:
                    if classification['keywords_matched']:
                        st.write("**Keywords Matched:**")
                        st.write(", ".join(classification['keywords_matched']))

                    st.write("**Reasoning:**")
                    st.write(classification['reasoning'])

                # Escalation results
                st.subheader("⚡ Escalation Analysis")
                escalation = result['escalation']

                if escalation['should_escalate']:
                    st.error(
                        f"🚨 Escalation Required: {escalation['escalation_level']}"
                    )
                    st.write(f"**Reason:** {escalation['description']}")
                    st.write(f"**Estimated Time:** {escalation['estimated_time']}")
                else:
                    st.success(
                        "✅ No escalation needed - can be handled by Level 1 support"
                    )

                # Knowledge response
                if result['knowledge_response']['available']:
                    st.subheader("💡 Knowledge Base Response")
                    knowledge = result['knowledge_response']

                    if knowledge['answer']:
                        st.info(knowledge['answer'])
                        st.write(f"**Confidence:** {knowledge['confidence']:.1%}")
                        st.write(f"**Sources Found:** {knowledge['sources_count']}")
                    else:
                        st.warning("No relevant knowledge found for this request")

                # Final recommendation
                st.subheader("📋 Recommendation")
                st.info(result['recommendation'])
        else:
            st.error("Please enter a request description")

with tab2:
    st.header("Request Classification Only")
    st.write("Test the classification system without full processing")

    classify_request = st.text_area(
        "Enter request to classify:", height=100, key="classify_input"
    )

    if st.button("🏷️ Classify Request"):
        if classify_request.strip():
            with st.spinner("Classifying..."):
                classification = (
                    st.session_state.helpdesk_api.classifier.classify_request(
                        classify_request
                    )
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Category",
                        classification.category.value.replace('_', ' ').title(),
                    )
                    st.metric("Confidence", f"{classification.confidence:.1%}")

                with col2:
                    if classification.keywords_matched:
                        st.write("**Keywords Matched:**")
                        for keyword in classification.keywords_matched:
                            st.code(keyword)

                st.write("**Reasoning:**")
                st.info(classification.reasoning)
        else:
            st.error("Please enter a request to classify")

with tab3:
    st.header("Knowledge Base Search")

    if st.session_state.helpdesk_api.knowledge_enabled:
        search_query = st.text_input(
            "Search knowledge base:", placeholder="Enter search terms..."
        )

        if st.button("🔍 Search Knowledge Base"):
            if search_query.strip():
                with st.spinner("Searching..."):
                    try:
                        results = (
                            st.session_state.helpdesk_api.retriever.search_knowledge(
                                search_query, n_results=5
                            )
                        )

                        if results:
                            st.success(f"Found {len(results)} relevant documents")

                            for i, result in enumerate(results, 1):
                                with st.expander(
                                    f"Result {i} - Relevance: {result.relevance_score:.1%}"
                                ):
                                    st.write(f"**Source:** {result.source}")
                                    st.write(
                                        f"**Type:** {result.metadata.get('type', 'Unknown')}"
                                    )
                                    st.write("**Content:**")
                                    st.write(
                                        result.content[:500] + "..."
                                        if len(result.content) > 500
                                        else result.content
                                    )
                        else:
                            st.warning("No relevant documents found")
                    except Exception as e:
                        st.error(f"Search failed: {e}")
            else:
                st.error("Please enter a search query")
    else:
        st.warning(
            "Knowledge base is not available. Please configure COHERE_API_KEY to enable this feature."
        )

with tab4:
    st.header("Request History")

    if st.session_state.request_history:
        # Clear history button
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.request_history = []
            st.rerun()

        st.write(f"**Total Requests:** {len(st.session_state.request_history)}")

        # Display history in reverse order (newest first)
        for i, entry in enumerate(reversed(st.session_state.request_history)):
            with st.expander(f"{entry['timestamp']} - {entry['result']['request_id']}"):
                st.write("**Request:**")
                st.write(entry['request'])

                st.write("**Classification:**")
                classification = entry['result']['classification']
                st.write(
                    f"Category: {classification['category']}, Confidence: {classification['confidence']:.1%}"
                )

                st.write("**Escalation:**")
                escalation = entry['result']['escalation']
                if escalation['should_escalate']:
                    st.write(f"⚠️ Escalated to {escalation['escalation_level']}")
                else:
                    st.write("✅ No escalation needed")

                st.write("**Recommendation:**")
                st.write(entry['result']['recommendation'])

                # Show raw JSON if needed
                if st.checkbox("Show raw data", key=f"raw_{i}"):
                    st.json(entry['result'])
    else:
        st.info(
            "No requests have been processed yet. Submit a request in the first tab to see history here."
        )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        IT Help Desk System v2.0 | Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
