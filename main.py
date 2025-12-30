import os
# Disable tqdm progress bars BEFORE any imports to avoid Windows stderr issues
os.environ['TQDM_DISABLE'] = '1'
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator, model_validator
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
import numpy as np
import scipy
from scipy.spatial.distance import cosine
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import json
import re

load_dotenv()

# Validate API key at startup
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY is not set. Please add it to your .env file. "
        "Get your API key from: https://console.anthropic.com/"
    )

app = FastAPI(title="AI Study Assistant", version="1.0.0")

# Configure logging with UTF-8 encoding for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

uploaded_documents = {}
conversations = {}

# Configuration constants
MAX_FILE_SIZE = 100 * 1024 * 1024   
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if not text:   
        return []
    
    if len(text) < chunk_size:
        return [text]
    
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk:
            chunks.append(chunk)
    
    return chunks


def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding for text, with Windows stderr workaround"""
    if not text:
        raise ValueError("Text cannot be empty")
    
    # Windows console workaround - temporarily redirect stderr to suppress tqdm errors
    import sys
    old_stderr = sys.stderr
    
    try:
        # Redirect stderr to devnull to avoid Windows console issues with tqdm
        sys.stderr = open(os.devnull, 'w')
        result = embedding_model.encode(text, show_progress_bar=False, convert_to_numpy=True)
        return result
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr

def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    return 1 - scipy.spatial.distance.cosine(embedding1, embedding2)

def find_relevant_chunks_semantic(
    question_embedding: np.ndarray,
    chunk_embeddings: list[np.ndarray],
    chunks: list[str],
    top_k: int = 3
) -> list[str]:
    top_chunks = []
    for chunk_embedding, chunk in zip(chunk_embeddings, chunks):
        score = calculate_similarity(question_embedding, chunk_embedding)
        top_chunks.append((score, chunk))

    top_chunks.sort(reverse=True)
    top_chunks = top_chunks[:top_k]

    return [chunk for score, chunk in top_chunks]

def get_document_embeddings(document_name: str) -> list[np.ndarray]:
    doc = uploaded_documents[document_name]
    if isinstance(doc, dict) and "embeddings" in doc:
        return doc["embeddings"]
    return []

def collect_all_document_data():
    """
    Collect all chunks, embeddings, and sources from all uploaded documents.
    
    Returns:
        tuple: (all_chunks, all_embeddings, all_sources)
    """
    all_chunks = []
    all_embeddings = []
    all_sources = []
    
    # Edge case: Empty uploaded_documents
    if not uploaded_documents:
        return all_chunks, all_embeddings, all_sources
    
    # Iterate through all documents
    for document_name in uploaded_documents.keys():
        chunks = get_document_chunks(document_name)
        embeddings = get_document_embeddings(document_name)
        
        # Add chunks, embeddings, and sources
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_sources.append(document_name)
            # Add embedding if available, otherwise empty list element
            if i < len(embeddings):
                all_embeddings.append(embeddings[i])
            else:
                all_embeddings.append(None)
    
    return all_chunks, all_embeddings, all_sources
    
def get_document_chunks(document_name: str) -> list[str]:
    """
    Get chunks from a document with backward compatibility.
    """
    doc = uploaded_documents[document_name]
    if isinstance(doc, dict):
        return doc["chunks"]
    return [doc]

def find_relevant_chunks(question: str, chunks: list[str], top_k: int = 3) -> list[str]:
    if not chunks:
        return []
    
    # Convert question to lowercase words
    question_words = set(question.lower().split())
    
    # Score each chunk
    scored_chunks = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        # Count how many question words appear in this chunk
        score = len(question_words & chunk_words)
        scored_chunks.append((score, chunk))
    
    # Sort by score (highest first)
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    
    # Return top K chunks (or all if fewer than K)
    return [chunk for _, chunk in scored_chunks[:top_k]]

class QuizRequest(BaseModel):
    num_questions: int
    difficulty: str
    document_name: Optional[str] = None
    use_all_documents: Optional[bool] = False
    
    @field_validator("num_questions")
    @classmethod
    def validate_num_questions(cls, v: int) -> int:
        if not (5 <= v <= 40):
            raise ValueError("You can't have less than 5 or more than 40 questions in your quiz.")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        difficulties = ["easy", "medium", "hard"]
        if v not in difficulties:
            raise ValueError(f"Difficulty must be one of: {', '.join(difficulties)}")
        return v
    
    @model_validator(mode='after')
    def validate_document_options(self):
        if self.document_name and self.use_all_documents:
            raise ValueError("Cannot specify both document_name and use_all_documents. Use one or the other.")
        return self

@app.post("/generate-quiz")
async def generate_quiz(request: QuizRequest):

    if request.use_all_documents:
        all_chunks, all_embeddings, all_sources = collect_all_document_data()
        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NoChunks",
                    "message": "No document chunks found. Documents may be empty.",
                }
            )
        # For all documents, use general quiz embedding
        quiz_embedding = generate_embedding("key concepts for quiz on all documents")
    else:
        if not request.document_name:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MissingDocumentName",
                    "message": "document_name is required when use_all_documents is False.",
                }
            )
        # Validate document exists
        if request.document_name not in uploaded_documents:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DocumentNotFound",
                    "message": f"Document '{request.document_name}' not found.",
                    "available": list(uploaded_documents.keys())
                }
            )
        all_chunks = get_document_chunks(request.document_name)
        all_embeddings = get_document_embeddings(request.document_name)
        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NoChunksOrEmbeddings",
                    "message": f"Document '{request.document_name}' has no chunks or embeddings.",
                }
            )
        # For single document, use document-specific embedding
        quiz_embedding = generate_embedding(f"key concepts for quiz on {request.document_name}")
    
    # Dynamic top_k based on number of questions (more questions = more context needed)
    # Use at least 5 chunks, up to 15 for larger quizzes
    top_k = min(max(request.num_questions, 5), 15)
    
    # Use semantic search if embeddings available, otherwise use first chunks
    if len(all_embeddings) > 0:
        relevant_chunks = find_relevant_chunks_semantic(quiz_embedding, all_embeddings, all_chunks, top_k=top_k)
    else:
        relevant_chunks = all_chunks[:top_k]  # Fallback to first chunks
    
    # Final fallback if still empty
    if not relevant_chunks: 
        relevant_chunks = all_chunks[:top_k]

    combined_text = "\n\n---\n\n".join(relevant_chunks)
    
    # Difficulty guidelines
    difficulty_guidelines = {
        "easy": "Questions should test basic recall of facts directly stated in the text. Focus on who, what, when, where questions.",
        "medium": "Questions should require understanding and application of concepts. Students must connect ideas and apply knowledge.",
        "hard": "Questions should require analysis, synthesis, and deep understanding. Students must evaluate, compare, and draw conclusions."
    }
    
    prompt = f"""You are creating a {request.difficulty} difficulty quiz.

Content to quiz on:
{combined_text}

Create {request.num_questions} questions.

{difficulty_guidelines[request.difficulty]}

IMPORTANT: The quiz must include BOTH question formats (approximately 50% each):

1. MULTIPLE CHOICE QUESTIONS:
   - Each question must have exactly 4 options (A, B, C, D)
   - Only one option is correct
   - Include clear explanations

2. SHORT ANSWER QUESTIONS:
   - Require students to type their answer
   - Provide the expected answer and key points
   - Include acceptable variations or alternative phrasings

Mix the question types throughout the quiz. Ensure questions test different aspects:
- Factual recall
- Conceptual understanding
- Application of concepts
- Analysis and synthesis

CRITICAL: Return ONLY valid JSON with this EXACT structure:
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "Question text here?",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct": "B",
      "explanation": "Brief explanation of why B is correct"
    }},
    {{
      "type": "short_answer",
      "question": "Question text here?",
      "correct_answer": "The expected answer or key points",
      "explanation": "Brief explanation or additional context",
      "acceptable_variations": ["Alternative phrasing 1", "Alternative phrasing 2"]
    }}
  ]
}}

Rules:
1. All questions must be answerable from the provided content
2. Mix multiple choice and short answer questions (approximately 50/50)
3. Multiple choice questions must have exactly 4 options (A, B, C, D)
4. Only one option is correct for multiple choice questions
5. Include clear explanations for all questions
6. Return ONLY the JSON, no other text

DO NOT include markdown code fences or any other formatting.
Return raw JSON only."""
    
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
    except Exception as e:
        logger.error(f"Error calling Claude API for quiz generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "QuizGenerationFailed",
                "message": "Failed to generate quiz. Please try again.",
                "detail": str(e)
            }
        )
    
    raw_response_text = response.content[0].text
    
    # Extract JSON from response (handle markdown code fences)
    if raw_response_text.startswith("```json"):
        raw_response_text = raw_response_text[len("```json"):].strip()
    elif raw_response_text.startswith("```"):
        raw_response_text = raw_response_text[len("```"):].strip()
    
    if raw_response_text.endswith("```"):
        raw_response_text = raw_response_text[:-len("```")].strip()
    
    # Try to extract JSON using regex if there's extra text
    json_match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
    else:
        json_str = raw_response_text
    
    # Parse JSON
    try:
        quiz_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse quiz JSON: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "JSONParseError",
                "message": "Failed to parse quiz response as JSON",
                "detail": str(e)
            }
        )
    
    # Validate quiz data structure
    if "questions" not in quiz_data:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "InvalidQuizFormat",
                "message": "Quiz data is not in the expected format.",
                "detail": "Expected 'questions' key in the quiz data."
            }
        )
    
    if not isinstance(quiz_data["questions"], list):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "InvalidQuizFormat",
                "message": "Quiz data is not in the expected format.",
                "detail": "Expected 'questions' to be a list."
            }
        )
    
    # Validate each question has required fields
    for i, q in enumerate(quiz_data["questions"]):
        if q.get("type") == "multiple_choice":
            required_fields = ["question", "options", "correct", "explanation"]
        elif q.get("type") == "short_answer":
            required_fields = ["question", "correct_answer", "explanation"]
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "InvalidQuizFormat",
                    "message": f"Question {i+1} has invalid type. Must be 'multiple_choice' or 'short_answer'."
                }
            )
        
        for field in required_fields:
            if field not in q:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "InvalidQuizFormat",
                        "message": f"Question {i+1} is missing required field: '{field}'."
                    }
                )
    
    # Determine document name for response
    document_name = request.document_name if request.document_name else "all_documents"
    
    # Return formatted response
    return {
        "success": True,
        "document": document_name,
        "difficulty": request.difficulty,
        "num_questions_requested": request.num_questions,
        "num_questions_generated": len(quiz_data["questions"]),
        "questions": quiz_data["questions"]
    }

class ChatRequest(BaseModel):
    message: str
    document_name: Optional[str] = None
    use_all_documents: Optional[bool] = False
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
    
    @model_validator(mode='after')
    def validate_document_options(self):
        """Validate that document_name and use_all_documents are not both set"""
        if self.document_name and self.use_all_documents:
            raise ValueError("Cannot specify both document_name and use_all_documents. Use one or the other.")
        return self


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # Get or create session
        session_id = request.session_id or "default"
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        # Build user message (with document if specified)
        user_message = request.message
        
        # Initialize metadata tracking
        documents_used = []
        chunk_sources = []
        
        if request.document_name:
            # Single document mode
            if request.document_name not in uploaded_documents:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "DocumentNotFound",
                        "message": f"Document '{request.document_name}' not found.",
                        "detail": f"Available: {list(uploaded_documents.keys())}"
                    }
                )
            all_chunks = get_document_chunks(request.document_name)
            all_embeddings = get_document_embeddings(request.document_name)
            
            # Edge case: Document has no chunks
            if not all_chunks:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "EmptyDocument",
                        "message": f"Document '{request.document_name}' has no chunks.",
                    }
                )
            
            if len(all_embeddings) > 0:
                question_embedding = generate_embedding(request.message)
                relevant_chunks = find_relevant_chunks_semantic(question_embedding, all_embeddings, all_chunks)
            else:
                relevant_chunks = find_relevant_chunks(request.message, all_chunks)

            # Fallback: If no relevant chunks found, use all chunks
            if not relevant_chunks:
                relevant_chunks = all_chunks

            # Track metadata for single document mode
            documents_used = [request.document_name]
            chunk_sources = [request.document_name] * len(relevant_chunks)

            combined_text = "\n\n---\n\n".join(relevant_chunks)
            
            # Edge case: Empty combined_text (shouldn't happen due to check above, but safety check)
            if not combined_text:
                combined_text = "No relevant content found in document."
            
            user_message = f"""Here are sections from the document:
{combined_text}

Based on these sections, answer: {request.message}

If not in document, say so."""
                    
        elif request.use_all_documents:
            # All documents mode - collect all documents (with or without embeddings)
            all_chunks, all_embeddings, all_sources = collect_all_document_data()
            
            # Collect chunks from ALL documents (not just those with embeddings)
            if not uploaded_documents:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "NoDocuments",
                        "message": "No documents uploaded. Please upload documents first.",
                    }
                )
            
            # Edge case: No chunks found in any document
            if not all_chunks:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "NoChunks",
                        "message": "No document chunks found. Documents may be empty.",
                    }
                )
            
            # Filter out None embeddings and track which chunks have embeddings
            chunks_with_embeddings = []
            embeddings_filtered = []
            sources_with_embeddings = []
            
            for chunk, embedding, source in zip(all_chunks, all_embeddings, all_sources):
                if embedding is not None:
                    chunks_with_embeddings.append(chunk)
                    embeddings_filtered.append(embedding)
                    sources_with_embeddings.append(source)
            
            # Use semantic search if we have embeddings, otherwise keyword search
            if len(embeddings_filtered) > 0:
                question_embedding = generate_embedding(request.message)
                relevant_chunks = find_relevant_chunks_semantic(question_embedding, embeddings_filtered, chunks_with_embeddings)
                # Get sources for the relevant chunks
                relevant_sources = []
                for chunk in relevant_chunks:
                    try:
                        idx = chunks_with_embeddings.index(chunk)
                        relevant_sources.append(sources_with_embeddings[idx])
                    except ValueError:
                        relevant_sources.append("unknown")
            else:
                # No embeddings available, use keyword search
                relevant_chunks = find_relevant_chunks(request.message, all_chunks)
                if not relevant_chunks:
                    relevant_chunks = all_chunks[:10]  # Limit to first 10 chunks if no matches
                
                
            chunk_to_source = dict(zip(all_chunks, all_sources))

            # Lookup
            relevant_sources = [chunk_to_source.get(chunk, "unknown") for chunk in relevant_chunks]
            
            # Edge case: Ensure we have sources for all chunks
            if len(relevant_sources) != len(relevant_chunks):
                while len(relevant_sources) < len(relevant_chunks):
                    relevant_sources.append("unknown")
            
            # Format chunks with sources
            formatted_chunks = []
            for chunk, source in zip(relevant_chunks, relevant_sources):
                formatted_chunks.append(f"Source: {source}\n--------------------------------\n{chunk}")
            
            combined_text = "\n\n---\n\n".join(formatted_chunks)
            
            # Track metadata for all documents mode
            chunk_sources = relevant_sources
            documents_used = list(set(relevant_sources))  # Get unique document names
            
            user_message = f"""Here are sections from the documents:
{combined_text}

Based on these sections, answer: {request.message}

If not in documents, say so."""
                    
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
            "message_count": len(conversations[session_id]),
            "documents_used": documents_used,
            "chunk_sources": chunk_sources
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
        try:
            logger.error(f"Chat error: {str(e)}")
        except:
            pass  # Ignore logging errors on Windows
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": "An unexpected error occurred.",
                "detail": str(e)
            }
        )

@app.post("/summarize/{filename}")
async def summarize_document(filename: str):
    if filename not in uploaded_documents:
        raise HTTPException(status_code = 404, detail = {"error": "DocumentNotFound", "message": f"Document {filename} not found", "available": list(uploaded_documents.keys())})
    doc = uploaded_documents[filename]
    if isinstance(doc, dict):
        text = doc["full_text"]
    else:
        text = doc
    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    if not text or len(text.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "EmptyDocument",
                "message": f"Document '{filename}' is empty."
            }
        )
    MAX_TEXT_LENGTH = 50000  # ~12,500 tokens
    if len(text) > MAX_TEXT_LENGTH:
        text_to_summarize = text[:MAX_TEXT_LENGTH] + "\n\n[Document truncated due to length]"
        logger.warning(f"Document {filename} truncated from {len(text)} to {MAX_TEXT_LENGTH} chars")
    else:
        text_to_summarize = text
    prompt = f"""Please analyze this document and provide a comprehensive summary.
    Document content:
    {text_to_summarize}

    Provide your summary in this format:

    **Main Topic:**
    [One sentence describing what this document is about]

    **Key Points:**
    - [First key concept or finding]
    - [Second key concept or finding]
    - [Third key concept or finding]
    - [Continue with other important points]

    **Important Details:**
    - [Significant details, definitions, or examples]
    - [Continue as needed]

    Keep it concise but comprehensive. Focus on the most important information a student would need to know."""
    try:
        # Step 6: Call Claude API
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt.strip()}]
        )
        
        summary = response.content[0].text
        
        # Step 7: Return the summary
        return {
            "filename": filename,
            "summary": summary,
            "original_length": len(text),
            "summarized_length": len(summary),
            "compression_ratio": f"{len(summary) / len(text) * 100:.1f}%"
        }
        
    except Exception as e:
        logger.error(f"Summarization error for {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SummarizationFailed",
                "message": "Failed to generate summary.",
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
        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        embeddings = [generate_embedding(chunk) for chunk in chunks]
        uploaded_documents[file.filename] = {
            "full_text": text,  # Keep original for reference
            "chunks": chunks,
            "embeddings": embeddings
        }
        logger.info(f"File uploaded successfully: {file.filename}")
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_type": file_type,
            "text_length": len(text),
            "chunk_count": len(chunks),
            "preview": text[:200],
            "embedding_count": len(embeddings)
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Log unexpected errors for debugging
        import traceback
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ProcessingError",
                "message": "An unexpected error occurred while processing the file",
                "detail": f"{str(e)}\n\n{error_trace}"
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

@app.get("/debug/chunks/{filename}")
async def debug_chunks(filename: str):
    # Debug endpoint to inspect chunking results.
    
    if filename not in uploaded_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = uploaded_documents[filename]
    chunks = get_document_chunks(filename)
    chunk_count = len(chunks)
    
    # Handle both dict (new format) and string (old format)
    if isinstance(doc, dict):
        total_length = len(doc["full_text"])
    else:
        total_length = len(doc)
    
    first_chunk_preview = chunks[0][:200] if chunks else ""
    
    # Get embeddings info
    embeddings = get_document_embeddings(filename)
    embedding_count = len(embeddings) if embeddings else 0
    has_embeddings = isinstance(doc, dict) and "embeddings" in doc and len(embeddings) > 0
    
    return {
        "filename": filename,
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
        "has_embeddings": has_embeddings,
        "first_chunk_preview": first_chunk_preview,
        "total_length": total_length
    }

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
