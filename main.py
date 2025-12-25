from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
import io
import anthropic
import logging
from anthropic import (
    APIError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
    BadRequestError,
    InternalServerError,
)
import os
from dotenv import load_dotenv

load_dotenv()

# Validate API key at startup
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY is not set. Please add it to your .env file. "
        "Get your API key from: https://console.anthropic.com/"
    )

app = FastAPI(title="AI Study Assistant", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

uploaded_documents = {}
conversations = {}

# Configuration constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB - prevents memory issues

class ChatRequest(BaseModel):
    message: str
    document_name: Optional[str] = None
    session_id: Optional[str] = None
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('document_name')
    @classmethod
    def validate_document_name(cls, v: Optional[str]) -> Optional[str]:
        # Only validate if document_name is provided (not None)
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Document name cannot be empty or whitespace only")
        return v

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Session ID cannot be empty")
        return v


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # Get or create session
        session_id = request.session_id or "default"
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        # Build user message (with document if specified)
        user_message = request.message
        
        if request.document_name:
            if request.document_name not in uploaded_documents:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "DocumentNotFound",
                        "message": f"Document '{request.document_name}' not found.",
                        "detail": f"Available: {list(uploaded_documents.keys())}"
                    }
                )
            
            document_text = uploaded_documents[request.document_name]
            user_message = f"""Here is a document:

<document>
{document_text}
</document>

Based on this document, answer: {request.message}

If not in document, say so."""
        
        # Build message history for Claude
        # Copy existing history and add new message
        message_history = conversations[session_id].copy()
        message_history.append({"role": "user", "content": user_message})
        
        # Send to Claude with full conversation context
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=message_history
        )
        
        assistant_message = response.content[0].text
        
        # Save conversation (both user and assistant messages)
        conversations[session_id].append({"role": "user", "content": user_message})
        conversations[session_id].append({"role": "assistant", "content": assistant_message})
        
        return {
            "response": assistant_message,
            "session_id": session_id,
            "message_count": len(conversations[session_id])
        }
    
    except HTTPException:
        raise
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "AuthenticationError",
                "message": "Invalid API key. Please check your ANTHROPIC_API_KEY in the .env file.",
                "detail": str(e)
            }
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "RateLimitError",
                "message": "Rate limit exceeded. Please wait a moment and try again.",
                "detail": str(e)
            }
        )
    except APIConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "APIConnectionError",
                "message": "Unable to connect to Anthropic API. Please check your internet connection.",
                "detail": str(e)
            }
        )
    except BadRequestError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "BadRequestError",
                "message": "Invalid request. Please check your request format.",
                "detail": str(e)
            }
        )
    except InternalServerError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "InternalServerError",
                "message": "Anthropic API is experiencing issues. Please try again later.",
                "detail": str(e)
            }
        )
    except APIStatusError as e:
        status_code = e.status_code if hasattr(e, 'status_code') else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "APIStatusError",
                "message": f"API returned an error (status {status_code}).",
                "detail": str(e)
            }
        )
    except APIError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "APIError",
                "message": "An error occurred while processing your request with the Anthropic API.",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": "An unexpected error occurred.",
                "detail": str(e)
            }
        )

@app.get("/documents")
async def get_all_documents():
    return {
        "documents": [
            {"filename": name, "length": len(text)}
            for name, text in uploaded_documents.items()
        ]
    }

@app.get("/documents/{filename}")
async def get_document(filename: str):
    if filename not in uploaded_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"filename": filename, "length": len(uploaded_documents[filename])}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    if filename not in uploaded_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    del uploaded_documents[filename]
    return {"message": "Document deleted successfully"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        
        # Validate file is not empty
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "EmptyFile",
                    "message": "File is empty. Please upload a file with content."
                }
            )
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "FileTooLarge",
                    "message": f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB",
                    "detail": f"Your file size: {len(content) / (1024*1024):.2f}MB"
                }
            )
        
        # Validate file type and process
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "InvalidFilename",
                    "message": "File must have a filename"
                }
            )
        
        if file.filename.endswith('.pdf'):
            try:
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                file_type = "pdf"
            except PdfReadError as e:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "InvalidPDF",
                        "message": "Invalid or corrupted PDF file",
                        "detail": str(e)
                    }
                )
        elif file.filename.endswith('.txt'):
            try:
                text = content.decode('utf-8')
                file_type = "txt"
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "EncodingError",
                        "message": "File encoding not supported. Use UTF-8 text files."
                    }
                )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "UnsupportedFileType",
                    "message": "Only PDF and TXT files are supported",
                    "detail": f"Received file type: {file.filename.split('.')[-1] if '.' in file.filename else 'unknown'}"
                }
            )
        
        uploaded_documents[file.filename] = text
        logger.info(f"File uploaded successfully: {file.filename} ({len(text)} characters)")
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_type": file_type,
            "text_length": len(text),
            "preview": text[:200]
        }
    except HTTPException:
        # Re-raise HTTPExceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Log unexpected errors for debugging
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ProcessingError",
                "message": "An unexpected error occurred while processing the file",
                "detail": str(e)
            }
        )

@app.get("/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a session."""
    if session_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    return {
        "session_id": session_id,
        "message_count": len(conversations[session_id]),
        "messages": conversations[session_id]
    }

@app.get("/conversations")
async def list_conversations():
    """List all active conversation sessions."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "message_count": len(messages)
            }
            for sid, messages in conversations.items()
        ]
    }

@app.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation session."""
    if session_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    del conversations[session_id]
    return {"message": "Conversation deleted successfully"}

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the Echo API", "endpoints": ["/echo"]}

@app.get("/echo")
async def echo(message: str):
    """
    Echo endpoint that takes a message parameter and returns it back.
    
    Args:
        message: The message to echo back
        
    Returns:
        The echoed message
    """
    return {"echoed_message": message}