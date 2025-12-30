"""
Chat Page - Q&A with Documents
"""

import streamlit as st
import sys
import os
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import (
    send_chat_message,
    get_documents,
    get_conversations,
    get_conversation,
    delete_conversation
)

# Page configuration
st.set_page_config(
    page_title="Chat",
    page_icon="💬",
    layout="wide"
)

# Initialize session state
if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = 'default'

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'chat_mode' not in st.session_state:
    st.session_state.chat_mode = "General Chat"

if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None

# Sidebar for session and document management
with st.sidebar:
    st.header("Chat Settings")

    # Session Management
    st.subheader("Session")

    # Get available sessions
    sessions_result = get_conversations()
    available_sessions = []
    if sessions_result["success"]:
        sessions_data = sessions_result["data"].get("sessions", [])
        available_sessions = [s["session_id"] for s in sessions_data]

    # Add current session if not in list
    if st.session_state.chat_session_id not in available_sessions:
        available_sessions.insert(0, st.session_state.chat_session_id)

    # Session selector
    current_session = st.selectbox(
        "Active Session",
        options=available_sessions,
        index=0 if st.session_state.chat_session_id in available_sessions else 0,
        help="Select or switch between conversation sessions"
    )

    # Update session if changed
    if current_session != st.session_state.chat_session_id:
        st.session_state.chat_session_id = current_session
        # Load conversation history
        history_result = get_conversation(current_session)
        if history_result["success"]:
            st.session_state.chat_history = history_result["data"].get("messages", [])
        else:
            st.session_state.chat_history = []
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Session", use_container_width=True):
            new_session_id = str(uuid.uuid4())[:8]
            st.session_state.chat_session_id = new_session_id
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        if st.button("🗑️ Delete", use_container_width=True):
            if st.session_state.chat_session_id != 'default' or len(st.session_state.chat_history) > 0:
                delete_result = delete_conversation(st.session_state.chat_session_id)
                if delete_result["success"]:
                    st.session_state.chat_session_id = 'default'
                    st.session_state.chat_history = []
                    st.success("Session deleted")
                    st.rerun()
            else:
                st.info("Cannot delete empty default session")

    st.markdown("---")

    # Document Mode Selection
    st.subheader("Document Mode")

    chat_mode = st.radio(
        "Select mode:",
        options=["General Chat", "Single Document", "All Documents"],
        index=["General Chat", "Single Document", "All Documents"].index(st.session_state.chat_mode),
        help="Choose how to interact with documents"
    )

    st.session_state.chat_mode = chat_mode

    # Document selector for single document mode
    if chat_mode == "Single Document":
        docs_result = get_documents()
        if docs_result["success"]:
            documents = docs_result["data"].get("documents", [])
            if documents:
                doc_names = [doc["filename"] for doc in documents]
                selected_doc = st.selectbox(
                    "Choose document:",
                    options=doc_names,
                    help="Select a document to chat with"
                )
                st.session_state.selected_document = selected_doc
            else:
                st.warning("No documents uploaded. Please upload documents first.")
                st.session_state.selected_document = None
        else:
            st.error("Failed to load documents")
            st.session_state.selected_document = None

    elif chat_mode == "All Documents":
        docs_result = get_documents()
        if docs_result["success"]:
            doc_count = len(docs_result["data"].get("documents", []))
            st.info(f"Using all {doc_count} document(s)")
        else:
            st.warning("Failed to load documents")

    st.markdown("---")

    # Session info
    st.subheader("Session Info")
    st.markdown(f"**ID:** `{st.session_state.chat_session_id}`")
    st.markdown(f"**Messages:** {len(st.session_state.chat_history)}")

# Main chat interface
st.title("💬 Chat with Documents")

# Load conversation history if not loaded
if not st.session_state.chat_history:
    history_result = get_conversation(st.session_state.chat_session_id)
    if history_result["success"]:
        st.session_state.chat_history = history_result["data"].get("messages", [])

# Display chat history
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        st.info("👋 Start a conversation! Ask me anything about your documents or just chat.")
    else:
        for msg in st.session_state.chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            with st.chat_message(role):
                st.markdown(content)

                # Show document sources for assistant messages
                if role == "assistant" and "documents_used" in msg:
                    docs_used = msg.get("documents_used", [])
                    if docs_used:
                        st.caption(f"📄 Sources: {', '.join(docs_used)}")

# Chat input
user_input = st.chat_input("Type your message here...", key="chat_input")

if user_input:
    # Validate document mode requirements
    if st.session_state.chat_mode == "Single Document" and not st.session_state.selected_document:
        st.error("Please select a document first or switch to a different mode.")
        st.stop()

    # Add user message to history
    user_message = {"role": "user", "content": user_input}
    st.session_state.chat_history.append(user_message)

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare API call parameters
    document_name = None
    use_all_documents = False

    if st.session_state.chat_mode == "Single Document":
        document_name = st.session_state.selected_document
    elif st.session_state.chat_mode == "All Documents":
        use_all_documents = True

    # Send message to backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_message(
                message=user_input,
                document_name=document_name,
                use_all_documents=use_all_documents,
                session_id=st.session_state.chat_session_id
            )

            if result["success"]:
                response_data = result["data"]
                response_text = response_data.get("response", "No response")

                # Display response
                st.markdown(response_text)

                # Show sources if available
                docs_used = response_data.get("documents_used", [])
                if docs_used:
                    st.caption(f"📄 Sources: {', '.join(docs_used)}")

                # Add assistant message to history
                assistant_message = {
                    "role": "assistant",
                    "content": response_text,
                    "documents_used": docs_used
                }
                st.session_state.chat_history.append(assistant_message)

            else:
                error_message = f"❌ Error: {result['error']}"
                st.error(error_message)

                # Add error to history
                assistant_message = {
                    "role": "assistant",
                    "content": error_message
                }
                st.session_state.chat_history.append(assistant_message)

    # Rerun to update chat display
    st.rerun()

# Tips section
st.markdown("---")
with st.expander("💡 Chat Tips", expanded=False):
    st.markdown("""
    ### Chat Modes

    **General Chat**
    - Have a conversation without document context
    - Useful for general questions or brainstorming

    **Single Document**
    - Focus on one specific document
    - Get answers based on a single source
    - Best for deep dive into one topic

    **All Documents**
    - Query across your entire document library
    - Useful for finding connections between documents
    - Great for comprehensive research

    ### Features
    - **Session Management**: Create multiple sessions to organize different topics
    - **Conversation History**: Full chat history is maintained per session
    - **Source Citations**: See which documents were used to answer your questions
    - **Semantic Search**: Uses AI embeddings to find the most relevant content

    ### Best Practices
    - Be specific in your questions for better answers
    - Use single document mode when you know the source
    - Use all documents mode for cross-document queries
    - Create new sessions for different topics to keep conversations organized
    """)
