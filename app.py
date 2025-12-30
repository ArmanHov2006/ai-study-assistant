"""
AI Study Assistant - Streamlit Frontend
Main entry point and landing page
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = 'default'

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None

if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}

if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False

# Main page content
st.title("📚 AI Study Assistant")
st.markdown("### Your intelligent companion for document-based learning")

st.markdown("---")

# Welcome section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Welcome!

    This application helps you study and learn from your documents using AI. Upload your study materials
    and leverage powerful tools to enhance your learning experience.

    ### Features:

    **📤 Upload Documents**
    - Upload PDF and TXT files
    - Manage your document library
    - Automatic text processing with semantic embeddings

    **💬 Chat with Documents**
    - Ask questions about your documents
    - Get AI-powered answers with source citations
    - Support for single document, multiple documents, or general chat
    - Maintain conversation history across sessions

    **📚 Study Tools**
    - **Summarize**: Get concise summaries of your documents
    - **Quiz**: Generate interactive quizzes to test your knowledge
      - Multiple choice and short answer questions
      - Adjustable difficulty levels
      - Instant grading with explanations
    """)

with col2:
    st.info("""
    ### Quick Start

    1. Use the sidebar to navigate between pages

    2. Start by uploading documents on the **Upload** page

    3. Chat with your documents on the **Chat** page

    4. Use **Study Tools** to summarize and create quizzes
    """)

st.markdown("---")

# Getting started guide
with st.expander("📖 Getting Started Guide", expanded=False):
    st.markdown("""
    ### Step-by-Step Guide

    #### 1. Upload Your Documents
    Navigate to the **Upload** page and:
    - Click "Browse files" to select a PDF or TXT file
    - Wait for the upload and processing to complete
    - View your uploaded documents in the list below

    #### 2. Chat with Your Documents
    Go to the **Chat** page and:
    - Select a chat mode (single document, all documents, or general chat)
    - Type your question in the message box
    - View AI-generated answers with document sources
    - Create and switch between different conversation sessions

    #### 3. Generate Summaries
    On the **Study Tools** page, **Summarize** tab:
    - Select a document from the dropdown
    - Click "Generate Summary"
    - Review the structured summary with key points

    #### 4. Take Practice Quizzes
    On the **Study Tools** page, **Quiz** tab:
    - Choose a document or use all documents
    - Set the number of questions (5-40)
    - Select difficulty level (easy, medium, hard)
    - Click "Generate Quiz"
    - Answer the questions and submit for instant grading

    ### Tips
    - Ensure the backend server is running before using the app
    - Upload multiple documents to enable the "all documents" feature
    - Use sessions in the Chat page to organize different topics
    - Try different difficulty levels in quizzes to challenge yourself
    """)

# System status
st.markdown("---")
st.markdown("### System Status")

# Check backend connection
from utils.api_client import get_documents

status = get_documents()
if status["success"]:
    doc_count = len(status["data"].get("documents", []))
    st.success(f"✅ Backend connected | {doc_count} document(s) uploaded")
else:
    st.error(f"❌ Backend connection failed: {status['error']}")
    st.info("💡 Make sure the FastAPI backend is running: `uvicorn main:app --reload`")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    Powered by Claude 3.5 Haiku | Built with Streamlit and FastAPI
</div>
""", unsafe_allow_html=True)
