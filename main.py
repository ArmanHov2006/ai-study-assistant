from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator
from PyPDF2 import PdfReader
import io
import anthropic
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

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

uploaded_documents = {}

class ChatRequest(BaseModel):
    message: str
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()

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
        if file.filename.endswith('.pdf'):
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            file_type = "pdf"
        elif file.filename.endswith('.txt'):
            text = content.decode('utf-8')
            file_type = "txt"
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        uploaded_documents[file.filename] = text
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_type": file_type,
            "text_length": len(text),
            "preview": text[:200]
        }
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
        detail="File encoding not supported. Use UTF-8 text files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@app.post("/chat")
async def chat(request: ChatRequest):
    # Check API key before making request
    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ConfigurationError",
                "message": "API key is not configured. Please check your .env file.",
                "detail": "ANTHROPIC_API_KEY environment variable is missing"
            }
        )
    
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": request.message}
            ]
        )
        return {"response": message.content[0].text}
    
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
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": "An unexpected error occurred.",
                "detail": str(e)
            }
        )

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