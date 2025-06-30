"""
Streamlit UI for Interactive Help Desk System
=============================================
Clean, user-friendly interface with admin mode for technical details.
"""

import os
from typing import Any, Dict

import streamlit as st

# Import your main system components
from main import HelpDeskSystem

# Page configuration
st.set_page_config(
    page_title="IT Help Desk Assistant",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #1f4e79, #2e7bcf);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #2e7bcf;
    }

    .user-message {
        background: #e3f2fd;
        border-radius: 15px 15px 5px 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1976d2;
        color: #1a1a1a !important;
    }

    .assistant-message {
        background: #f1f8e9;
        border-radius: 15px 15px 15px 5px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #388e3c;
        color: #1a1a1a !important;
    }

    @media (prefers-color-scheme: dark) {
        .assistant-message {
            background: #2d4a2d;
            color: #e8f5e8 !important;
        }

        .user-message {
            background: #1e3a5f;
            color: #e3f2fd !important;
        }
    }

    .stApp[data-theme="dark"] .assistant-message {
        background: #2d4a2d;
        color: #e8f5e8 !important;
    }

    .stApp[data-theme="dark"] .user-message {
        background: #1e3a5f;
        color: #e3f2fd !important;
    }

    .admin-panel {
        background: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-ready { background-color: #4caf50; }
    .status-processing { background-color: #ff9800; }
    .status-error { background-color: #f44336; }

    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }

    .quick-action-btn {
        background: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s;
    }

    .quick-action-btn:hover {
        background: #2196f3;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "system_initialized" not in st.session_state:
        st.session_state.system_initialized = False
    if "help_desk_system" not in st.session_state:
        st.session_state.help_desk_system = None
    if "admin_mode" not in st.session_state:
        st.session_state.admin_mode = False
    if "system_status" not in st.session_state:
        st.session_state.system_status = "not_initialized"
    if "processing_query" not in st.session_state:
        st.session_state.processing_query = False


def initialize_system():
    """Initialize the help desk system."""
    if st.session_state.system_initialized:
        return True

    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        st.error("❌ COHERE_API_KEY environment variable not set")
        return False

    try:
        with st.spinner("🔧 Initializing Help Desk System..."):
            st.session_state.help_desk_system = HelpDeskSystem(api_key)

        if st.session_state.help_desk_system.is_ready:
            st.session_state.system_initialized = True
            st.session_state.system_status = "ready"
            st.success("✅ System initialized successfully!")
            return True
        else:
            st.session_state.system_status = "error"
            st.error("❌ System initialization failed")
            return False

    except Exception as e:
        st.session_state.system_status = "error"
        st.error(f"❌ Initialization error: {str(e)}")
        return False


def get_status_indicator():
    """Get status indicator HTML."""
    status_map = {
        "not_initialized": ("⚪", "System not initialized"),
        "ready": ("🟢", "System ready"),
        "processing": ("🟡", "Processing..."),
        "error": ("🔴", "System error"),
    }

    icon, text = status_map.get(st.session_state.system_status, ("⚪", "Unknown"))
    return f"{icon} {text}"


def display_quick_actions():
    """Display quick action buttons."""
    st.markdown("### Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔑 Password Reset", use_container_width=True, key="btn_password"):
            return "I forgot my password and can't log into my computer"

    with col2:
        if st.button("🌐 Network Issues", use_container_width=True, key="btn_network"):
            return "My internet connection is not working"

    with col3:
        if st.button("💻 Software Help", use_container_width=True, key="btn_software"):
            return "How do I install new software on my computer?"

    col4, col5, col6 = st.columns(3)

    with col4:
        if st.button("🔒 Security Issue", use_container_width=True, key="btn_security"):
            return "I think my computer might be compromised"

    with col5:
        if st.button("📧 Email Problems", use_container_width=True, key="btn_email"):
            return "I can't access my email account"

    with col6:
        if st.button("🖨️ Printer Issues", use_container_width=True, key="btn_printer"):
            return "My printer is not working"

    return None


def display_admin_panel(result: Dict[str, Any]):
    """Display admin panel with technical details."""
    if not st.session_state.admin_mode:
        return

    with st.expander("🔧 Admin Panel - Technical Details", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Classification Details**")
            cls = result["classification"]
            st.write(f"• **Category:** {cls['category'].replace('_', ' ').title()}")
            st.write(f"• **Confidence:** {cls['confidence']:.3f}")
            st.write(f"• **Keywords:** {', '.join(cls['keywords_matched'])}")
            st.write(f"• **Reasoning:** {cls['reasoning']}")

        with col2:
            st.markdown("**System Metrics**")
            esc = result["escalation"]
            kr = result["knowledge_response"]

            st.write(f"• **Request ID:** {result['request_id']}")
            st.write(
                f"• **Escalation Required:** {'Yes' if esc['should_escalate'] else 'No'}"
            )
            if esc["should_escalate"]:
                st.write(f"• **Escalation Level:** {esc['escalation_level']}")
                st.write(f"• **Priority:** {esc['priority']}")
            st.write(f"• **Response Confidence:** {kr['confidence']:.3f}")
            st.write(f"• **Sources Used:** {kr['sources_used']}")


def process_user_query(query: str):
    """Process user query and return response."""
    if not st.session_state.system_initialized:
        return None

    st.session_state.system_status = "processing"
    st.session_state.processing_query = True

    try:
        result = st.session_state.help_desk_system.process_request(query)
        st.session_state.system_status = "ready"
        st.session_state.processing_query = False
        return result

    except Exception as e:
        st.session_state.system_status = "error"
        st.session_state.processing_query = False
        st.error(f"Error processing request: {str(e)}")
        return None


def display_chat_message(role: str, content: str, result: Dict[str, Any] = None):
    """Display a chat message with appropriate styling."""

    if role == "user":
        st.markdown(
            f"""
        <div class="user-message">
            <strong>You:</strong><br>
            {content}
        </div>
        """,
            unsafe_allow_html=True,
        )

    else:  # assistant
        st.markdown(
            f"""
        <div class="assistant-message">
            <strong>IT Assistant:</strong><br>
            {content}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Show admin panel if enabled
        if result:
            display_admin_panel(result)


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.markdown(
        """
    <div class="main-header">
        <h1>🔧 IT Help Desk Assistant</h1>
        <p>Your intelligent IT support companion</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.markdown("### System Status")
        st.markdown(get_status_indicator())

        st.markdown("---")

        # Admin mode toggle
        st.session_state.admin_mode = st.checkbox(
            "🔧 Admin Mode", value=st.session_state.admin_mode
        )

        if st.session_state.admin_mode:
            st.markdown("*Admin mode shows technical details*")

        st.markdown("---")

        # System controls
        if st.button("🔄 Reinitialize System"):
            st.session_state.system_initialized = False
            st.session_state.help_desk_system = None
            st.session_state.system_status = "not_initialized"
            st.rerun()

        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

        # Statistics (if admin mode)
        if st.session_state.admin_mode and st.session_state.messages:
            st.markdown("---")
            st.markdown("### Session Stats")
            total_messages = len(st.session_state.messages)
            user_messages = sum(
                1 for msg in st.session_state.messages if msg["role"] == "user"
            )
            st.metric("Total Messages", total_messages)
            st.metric("User Queries", user_messages)

    # Initialize system if not already done
    if not st.session_state.system_initialized:
        if not initialize_system():
            # Show retry button if initialization failed
            if st.button("🔄 Try Initialize Again"):
                st.rerun()
            return

    # Main content area
    if st.session_state.system_initialized:

        # Quick actions
        with st.container():
            quick_query = display_quick_actions()

        st.markdown("---")

        # Chat interface
        st.markdown("### 💬 Chat with IT Assistant")

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(
                    message["role"], message["content"], message.get("result")
                )

        # Chat input - use form to prevent constant resubmission
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Type your IT support question here...",
                value=quick_query if quick_query else "",
                key="user_query",
            )
            submit_button = st.form_submit_button("Send")

        # Process input when form is submitted
        if submit_button and user_input and not st.session_state.processing_query:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Process the query
            with st.spinner("🤔 Thinking..."):
                result = process_user_query(user_input)

            if result and "error" not in result:
                # Extract clean response for user
                response_text = result["knowledge_response"]["answer"]

                # Add assistant response to chat
                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text, "result": result}
                )

                # Check for escalation (show to user if needed)
                if result["escalation"]["should_escalate"]:
                    escalation_msg = f"""
                    ⚠️ **This issue requires immediate attention:**
                    - Priority: {result['escalation']['priority']}
                    - Contact: {result['escalation']['contact_info']}
                    - Please follow up with the appropriate team.
                    """

                    st.session_state.messages.append(
                        {"role": "assistant", "content": escalation_msg}
                    )

            elif result and "error" in result:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"I apologize, but I encountered an error: {result['error']}",
                    }
                )

            # Rerun to display new messages
            st.rerun()

        # Show processing status
        if st.session_state.processing_query:
            st.info("⏳ Processing your request...")

    else:
        st.warning("⚠️ System not initialized. Please check your configuration.")

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        IT Help Desk Assistant | Powered by AI |
        <span style="color: #2e7bcf;">Always here to help! 🚀</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
