"""
API Client for AI Study Assistant Backend
Handles all HTTP communication with the FastAPI backend
"""

import requests
import os
from typing import Optional, Dict, Any, List

# Backend configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _make_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """
    Internal helper for making HTTP requests with error handling

    Args:
        method: HTTP method (get, post, delete)
        endpoint: API endpoint path
        **kwargs: Additional arguments for requests

    Returns:
        Dict with success, data, and error fields
    """
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.request(method, url, timeout=30, **kwargs)

        # Check for HTTP errors
        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            return {
                "success": False,
                "data": None,
                "error": error_data.get("message", f"HTTP {response.status_code} error")
            }

        # Success
        return {
            "success": True,
            "data": response.json() if response.content else {},
            "error": None
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "data": None,
            "error": "Cannot connect to backend server. Make sure it's running on " + BACKEND_URL
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "data": None,
            "error": "Request timed out. The server might be busy."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "data": None,
            "error": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Unexpected error: {str(e)}"
        }


# Document Management Functions

def upload_document(file) -> Dict[str, Any]:
    """
    Upload a document to the backend

    Args:
        file: File object from Streamlit file_uploader

    Returns:
        Response dict with success status, data (filename, chunk_count, etc.), and error
    """
    try:
        files = {"file": (file.name, file, file.type)}
        return _make_request("post", "/upload", files=files)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Error preparing upload: {str(e)}"
        }


def get_documents() -> Dict[str, Any]:
    """
    Get list of all uploaded documents

    Returns:
        Response dict with success status and data containing documents list
    """
    return _make_request("get", "/documents")


def delete_document(filename: str) -> Dict[str, Any]:
    """
    Delete a document from the backend

    Args:
        filename: Name of the document to delete

    Returns:
        Response dict with success status and confirmation message
    """
    return _make_request("delete", f"/documents/{filename}")


# Chat Functions

def send_chat_message(
    message: str,
    document_name: Optional[str] = None,
    use_all_documents: bool = False,
    session_id: str = "default"
) -> Dict[str, Any]:
    """
    Send a chat message to the backend

    Args:
        message: User's message/question
        document_name: Optional single document to query
        use_all_documents: Whether to use all documents for context
        session_id: Chat session identifier

    Returns:
        Response dict with assistant's response, session info, and document sources
    """
    payload = {
        "message": message,
        "session_id": session_id
    }

    if document_name:
        payload["document_name"] = document_name
    if use_all_documents:
        payload["use_all_documents"] = True

    return _make_request("post", "/chat", json=payload)


def get_conversations() -> Dict[str, Any]:
    """
    Get list of all conversation sessions

    Returns:
        Response dict with list of sessions and their message counts
    """
    return _make_request("get", "/conversations")


def get_conversation(session_id: str) -> Dict[str, Any]:
    """
    Get conversation history for a specific session

    Args:
        session_id: Session identifier

    Returns:
        Response dict with full conversation history
    """
    return _make_request("get", f"/conversations/{session_id}")


def delete_conversation(session_id: str) -> Dict[str, Any]:
    """
    Delete a conversation session

    Args:
        session_id: Session identifier to delete

    Returns:
        Response dict with success confirmation
    """
    return _make_request("delete", f"/conversations/{session_id}")


# Study Tools Functions

def summarize_document(filename: str) -> Dict[str, Any]:
    """
    Generate a summary for a document

    Args:
        filename: Name of the document to summarize

    Returns:
        Response dict with summary text and compression metrics
    """
    return _make_request("post", f"/summarize/{filename}")


def generate_quiz(
    num_questions: int,
    difficulty: str,
    document_name: Optional[str] = None,
    use_all_documents: bool = False
) -> Dict[str, Any]:
    """
    Generate a quiz from documents

    Args:
        num_questions: Number of questions to generate (5-40)
        difficulty: Difficulty level (easy, medium, hard)
        document_name: Optional single document to use
        use_all_documents: Whether to use all documents

    Returns:
        Response dict with quiz questions in mixed format
    """
    payload = {
        "num_questions": num_questions,
        "difficulty": difficulty
    }

    if document_name:
        payload["document_name"] = document_name
    if use_all_documents:
        payload["use_all_documents"] = True

    return _make_request("post", "/generate-quiz", json=payload)
