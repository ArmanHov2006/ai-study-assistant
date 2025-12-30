"""
Upload Page - Document Upload and Management
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import upload_document, get_documents, delete_document

# Page configuration
st.set_page_config(
    page_title="Upload Documents",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Upload Documents")
st.markdown("Upload PDF or TXT files to build your document library")

# File upload section
st.markdown("### Upload New Document")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'txt'],
    help="Supported formats: PDF, TXT (Max size: 10MB)",
    key="file_uploader"
)

if uploaded_file is not None:
    # Check file size (10MB = 10 * 1024 * 1024 bytes)
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > 10:
        st.error(f"❌ File too large: {file_size_mb:.2f}MB. Maximum size is 10MB.")
    else:
        # Show file info
        st.info(f"📄 **{uploaded_file.name}** ({file_size_mb:.2f}MB)")

        # Upload button
        if st.button("Upload Document", type="primary"):
            with st.spinner("Uploading and processing document..."):
                # Upload the file
                result = upload_document(uploaded_file)

                if result["success"]:
                    data = result["data"]
                    st.success(f"✅ Successfully uploaded **{data['filename']}**")

                    # Show upload details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Text Length", f"{data.get('text_length', 0):,} chars")
                    with col2:
                        st.metric("Chunks Created", data.get('chunk_count', 0))
                    with col3:
                        st.metric("Embeddings", data.get('embedding_count', 0))

                    # Show preview
                    if 'preview' in data:
                        with st.expander("📖 Document Preview"):
                            st.text(data['preview'])

                    # Rerun to refresh document list
                    st.rerun()
                else:
                    st.error(f"❌ Upload failed: {result['error']}")

st.markdown("---")

# Document list section
st.markdown("### 📄 Uploaded Documents")

# Fetch documents
with st.spinner("Loading documents..."):
    result = get_documents()

if not result["success"]:
    st.error(f"❌ Failed to load documents: {result['error']}")
    st.stop()

documents = result["data"].get("documents", [])

if not documents:
    st.info("📭 No documents uploaded yet. Upload your first document above!")
else:
    st.markdown(f"**Total documents:** {len(documents)}")
    st.markdown("")

    # Display each document
    for doc in documents:
        filename = doc.get("filename", "Unknown")
        length = doc.get("length", 0)

        # Create a container for each document
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"**📄 {filename}**")

            with col2:
                st.markdown(f"*{length:,} characters*")

            with col3:
                # Delete button with confirmation
                delete_key = f"delete_{filename}"
                if st.button("🗑️ Delete", key=delete_key, help=f"Delete {filename}"):
                    # Use session state for confirmation
                    st.session_state[f"confirm_{filename}"] = True

            # Confirmation dialog
            if st.session_state.get(f"confirm_{filename}", False):
                st.warning(f"⚠️ Are you sure you want to delete **{filename}**?")
                col_a, col_b, col_c = st.columns([1, 1, 4])

                with col_a:
                    if st.button("Yes, delete", key=f"confirm_yes_{filename}", type="primary"):
                        with st.spinner(f"Deleting {filename}..."):
                            delete_result = delete_document(filename)

                            if delete_result["success"]:
                                st.success(f"✅ Deleted {filename}")
                                # Clean up session state
                                if f"confirm_{filename}" in st.session_state:
                                    del st.session_state[f"confirm_{filename}"]
                                st.rerun()
                            else:
                                st.error(f"❌ Delete failed: {delete_result['error']}")

                with col_b:
                    if st.button("Cancel", key=f"confirm_no_{filename}"):
                        # Clean up session state
                        if f"confirm_{filename}" in st.session_state:
                            del st.session_state[f"confirm_{filename}"]
                        st.rerun()

            st.markdown("---")

# Add spacing at bottom
st.markdown("")
st.markdown("")

# Tips section
with st.expander("💡 Tips", expanded=False):
    st.markdown("""
    - **Supported formats:** PDF and TXT files
    - **Maximum file size:** 10MB
    - **Processing:** Documents are automatically chunked and embedded for semantic search
    - **Chunks:** Text is split into 1000-character segments with 200-character overlap
    - **Embeddings:** Each chunk is converted to a semantic vector for intelligent retrieval
    - **Deletion:** Deleting a document will remove it from all features (chat, quiz, summarize)
    """)
