# AI Study Assistant

An intelligent study assistant API powered by AI to help students with learning, note-taking, and academic support.

## 📋 Project Description

AI Study Assistant is a web API designed to provide intelligent study support through AI-powered features. The project aims to assist students with various learning tasks, including content summarization, question answering, and personalized study recommendations.

**Status:** 🚧 In Active Development (Day 1)

## 🛠️ Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs with Python
- **OpenAI** - AI integration for intelligent study assistance (planned)
- **Uvicorn** - ASGI server for running FastAPI applications
- **Python 3.13+** - Programming language

## 🚀 Setup Instructions

### Prerequisites

- Python 3.13 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd ai-study-assistant
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   
   On Windows (PowerShell):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   On Windows (Command Prompt):
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the development server**:
   ```bash
   uvicorn main:app --reload
   ```

6. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive API Documentation: `http://localhost:8000/docs`
   - Alternative API Documentation: `http://localhost:8000/redoc`

## 📊 Current Status

**Day 1 - Building the Foundation**

- ✅ Project structure initialized
- ✅ FastAPI application setup
- ✅ Basic API endpoints implemented
- ✅ Development environment configured
- 🔄 OpenAI integration (in progress)
- 🔄 Core study assistant features (planned)

## 📝 API Endpoints

### Current Endpoints

- `GET /` - Welcome message and API information
- `GET /echo?message=<text>` - Echo endpoint for testing

### Planned Endpoints

- Study content analysis
- Question answering
- Note summarization
- Study recommendations

## 🔧 Development

The server runs with auto-reload enabled by default. Any changes to `main.py` will automatically restart the server.

To stop the server, press `Ctrl+C` in the terminal.

## 📄 License

[To be determined]

---

**Note:** This project is in early development. Features and documentation will be updated as development progresses.

