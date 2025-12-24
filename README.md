# AI Study Assistant

An intelligent study assistant API powered by AI to help students with learning, note-taking, and academic support.

## 📋 Project Description

AI Study Assistant is a web API designed to provide intelligent study support through AI-powered features. The project aims to assist students with various learning tasks, including content summarization, question answering, and personalized study recommendations.

**Status:** 🚧 In Active Development (Day 1)

## 🛠️ Tech Stack

- **FastAPI** - Python web framework
- **Anthropic Claude API** - AI responses (Claude Haiku)
- **PyPDF2** - PDF text extraction
- **Python 3.8+** - Programming language

## 🚀 Setup

1. Clone the repo
2. Install: `pip install -r requirements.txt`
3. Create `.env` with `ANTHROPIC_API_KEY=your-key`
4. Run: `uvicorn main:app --reload`
5. Test: `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Hello"}'`

**Access the API:**

- API Base URL: `http://localhost:8000`
- Interactive API Documentation: `http://localhost:8000/docs`
- Alternative API Documentation: `http://localhost:8000/redoc`

## 📊 Current Status

### Features

- ✅ Echo endpoint (test)
- ✅ Claude API integration
- ✅ Chat endpoint (send message, get AI response)
- ✅ Document upload (PDF and TXT files)
- ✅ Document management (list, get, delete documents)
- ✅ **Document Q&A** - Ask questions about uploaded documents
- ✅ Comprehensive error handling

## 📝 API Endpoints

## 📚 Document Q&A Feature

### How it works
1. Upload a document (PDF or TXT) using `/upload`
2. Ask questions about it using `/chat` with `document_name` parameter
3. Claude answers based on your document content

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
  "response": "Claude's answer based on document context"
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
