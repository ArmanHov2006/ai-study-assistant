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
- ✅ Comprehensive error handling

## 📝 API Endpoints

#### POST /chat

Send a message and get Claude's response.

**Request:**

```json
{
  "message": "Your question here"
}
```

**Response:**

```json
{
  "response": "Claude's response here"
}
```

#### POST /upload

Upload a PDF or TXT file for processing.

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
