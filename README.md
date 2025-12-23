# AI Study Assistant

An intelligent study assistant API powered by AI to help students with learning, note-taking, and academic support.

## 📋 Project Description

AI Study Assistant is a web API designed to provide intelligent study support through AI-powered features. The project aims to assist students with various learning tasks, including content summarization, question answering, and personalized study recommendations.

**Status:** 🚧 In Active Development (Day 1)

## 🛠️ Tech Stack

- **FastAPI** - Python web framework
- **Anthropic Claude API** - AI responses
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
