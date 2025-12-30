# AI Study Assistant

An intelligent study assistant powered by AI to help students with learning, note-taking, and academic support.

## 📋 Project Description

AI Study Assistant is a full-stack application designed to provide intelligent study support through AI-powered features. Upload your documents and leverage powerful tools including document Q&A, summarization, and interactive quiz generation.

**Status:** ✅ Fully Functional with Web UI

## 🛠️ Tech Stack

**Backend:**
- **FastAPI** - Python web framework
- **Anthropic Claude API** - AI responses (Claude 3.5 Haiku)
- **PyPDF2** - PDF text extraction
- **SentenceTransformers** - Semantic embeddings for RAG
- **Python 3.8+** - Programming language

**Frontend:**
- **Streamlit** - Interactive web interface
- **Multi-page app architecture** - Upload, Chat, Study Tools

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-study-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

### Running the Application

You need to run both the backend and frontend:

**Terminal 1 - Start the Backend (FastAPI):**
```bash
uvicorn main:app --reload
```
The backend will run at `http://localhost:8000`

**Terminal 2 - Start the Frontend (Streamlit):**
```bash
streamlit run app.py
```
The frontend will automatically open at `http://localhost:8501`

### Access Points

- **Streamlit Web UI**: `http://localhost:8501` ✨ (Recommended for most users)
- **FastAPI Backend**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Alternative API Docs**: `http://localhost:8000/redoc`

## 📊 Features

### 📤 Document Upload & Management
- Upload PDF and TXT files (max 10MB)
- View all uploaded documents
- Delete documents from your library
- Automatic text extraction and processing

### 💬 Intelligent Chat
- **Three modes:**
  - Single Document - Focus on one document
  - All Documents - Query your entire library
  - General Chat - Conversation without document context
- Session management - Organize conversations by topic
- Full conversation history
- Source citations - See which documents were used

### 📚 Study Tools

**Summarize:**
- Generate comprehensive summaries
- Structured output with key points
- Compression metrics

**Quiz:**
- Interactive quiz generation
- Mixed question types (multiple choice + short answer)
- Three difficulty levels (easy, medium, hard)
- 5-40 questions per quiz
- Instant grading with explanations
- Support for single or all documents

### 🤖 AI-Powered Backend
- RAG (Retrieval-Augmented Generation) system
- Semantic search with embeddings
- Document chunking for efficient processing
- Claude 3.5 Haiku integration
- Comprehensive error handling

## 🎨 Streamlit Frontend

The Streamlit frontend provides an intuitive web interface with three main pages:

### 1. 📤 Upload Page
- Drag-and-drop file upload
- Document library with delete functionality
- Upload progress and feedback
- File validation

### 2. 💬 Chat Page
- Clean chat interface
- Sidebar controls for:
  - Session selection and management
  - Document mode selection
  - Document picker
- Real-time AI responses
- Source attribution

### 3. 📚 Study Tools Page

**Summarize Tab:**
- Document selector
- One-click summary generation
- Formatted output with metrics

**Quiz Tab:**
- Configurable quiz parameters
- Interactive question interface
- Submit and grade functionality
- Detailed feedback with explanations

## 📝 API Endpoints (Backend)

## 📚 Document Q&A Feature with RAG

### How it works
1. Upload a document (PDF or TXT) using `/upload` - document is automatically chunked
2. Ask questions about it using `/chat` with `document_name` parameter
3. System retrieves only relevant chunks (smart retrieval)
4. Claude answers based on relevant document sections

### RAG (Retrieval-Augmented Generation)
The system uses RAG to efficiently handle large documents:
- **Chunking**: Documents are split into 1000-character chunks with 200-character overlap
- **Smart Retrieval**: Only the 3 most relevant chunks are sent to Claude based on your question
- **Efficiency**: Saves tokens, reduces costs, and improves response speed
- **Accuracy**: Focuses on relevant content, improving answer quality

### Example Workflow

**Step 1: Upload document**
```bash
curl -X POST http://localhost:8000/upload -F "file=@notes.pdf"
```

**Step 2: Ask question about document**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main points?",
    "document_name": "notes.pdf"
  }'
```

**Step 3: Normal chat (no document)**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

### API Changes

#### POST /chat (Updated)
Now accepts optional `document_name` parameter for document-based questions.

**Request:**
```json
{
  "message": "Your question",
  "document_name": "optional_document.pdf"
}
```

**Response:**
```json
{
  "response": "Claude's answer based on document context",
  "session_id": "default",
  "message_count": 2
}
```

**Note:** If `document_name` is provided but doesn't exist, you'll get a 404 error with available documents listed.

#### POST /upload

Upload a PDF or TXT file for processing. Uploaded documents can then be used in chat queries.

**Request:**
```
POST /upload
Content-Type: multipart/form-data

file: [your file]
```

**Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "document.pdf",
  "file_type": "pdf",
  "text_length": 1234,
  "chunk_count": 5,
  "preview": "First 200 characters..."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/upload -F "file=@notes.pdf"
```

#### GET /documents

List all uploaded documents.

**Response:**
```json
{
  "documents": [
    {"filename": "doc1.pdf", "length": 1234},
    {"filename": "doc2.txt", "length": 567}
  ]
}
```

#### GET /documents/{filename}

Get a specific document's content.

**Response:**
```json
{
  "filename": "document.pdf",
  "length": 1234
}
```

#### DELETE /documents/{filename}

Delete an uploaded document.

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

#### GET /chat with Session ID

Maintain conversation context across multiple messages.

**Request:**
```json
{
  "message": "What is DNA?",
  "document_name": "biology.pdf",
  "session_id": "my_session_123"
}
```

**Response:**
```json
{
  "response": "DNA is...",
  "session_id": "my_session_123",
  "message_count": 4
}
```

#### GET /conversations

List all active conversation sessions.

**Response:**
```json
{
  "sessions": [
    {"session_id": "session1", "message_count": 6},
    {"session_id": "session2", "message_count": 2}
  ]
}
```

#### GET /conversations/{session_id}

Get conversation history for a specific session.

**Response:**
```json
{
  "session_id": "session1",
  "message_count": 6,
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}
```

#### DELETE /conversations/{session_id}

Delete a conversation session.

#### GET /debug/chunks/{filename}

Debug endpoint to inspect chunking results.

**Response:**
```json
{
  "filename": "document.pdf",
  "chunk_count": 5,
  "first_chunk_preview": "First 200 characters of first chunk...",
  "total_length": 5000
}
```

#### GET /echo

Echo endpoint for testing.

**Request:**
```
GET /echo?message=your_message
```

**Response:**
```json
{
  "echoed_message": "your_message"
}
```

## 🔧 Development

The server runs with auto-reload enabled by default. Any changes to `main.py` will automatically restart the server.

To stop the server, press `Ctrl+C` in the terminal.

## 📄 License

[To be determined]

---

**Note:** This project is in early development. Features and documentation will be updated as development progresses.
