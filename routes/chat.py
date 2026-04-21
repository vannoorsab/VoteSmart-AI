"""
AI Chat Route
Handles election Q&A using Google Gemini AI
"""

import logging
from typing import Optional
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach
from config import (
    MAX_MESSAGE_LENGTH,
    MIN_MESSAGE_LENGTH,
    CHAT_REQUESTS_PER_MINUTE,
)
from services.gemini_service import get_gemini_service
from services.firebase_service import get_firebase_service

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def _sanitize_input(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.

    Args:
        text: User input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text or empty string if invalid
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove leading/trailing whitespace
    text = text.strip()

    # Check length
    if len(text) < MIN_MESSAGE_LENGTH or len(text) > max_length:
        return ""

    # Use bleach to remove any HTML/scripts
    text = bleach.clean(text, tags=[], strip=True)

    return text


@chat_bp.route("/api/chat", methods=["POST"])
@limiter.limit(f"{CHAT_REQUESTS_PER_MINUTE}/minute")
def chat() -> tuple[dict, int]:
    """
    Generate AI response to election questions.

    Request body:
    {
        "message": "How do elections work in India?",
        "history": [{"role": "user", "content": "..."}, ...],
        "country": "india",  # optional
        "session_id": "abc123"  # optional for Firebase
    }

    Returns:
        JSON with 'response' field containing AI-generated answer
    """
    try:
        # Parse request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(force=True)
        user_message = data.get("message", "").strip()
        history = data.get("history", [])
        country = data.get("country", "").lower()
        session_id = data.get("session_id", "")

        # Validate input
        user_message = _sanitize_input(user_message)
        if not user_message:
            logger.warning("Empty or invalid message received")
            return jsonify({"error": "Message is required and must be 1-500 characters"}), 400

        # Get services
        gemini_service = get_gemini_service()
        firebase_service = get_firebase_service()

        # Generate response
        response_text = gemini_service.generate_response(
            user_message=user_message,
            history=history,
            temperature=0.7,
        )

        if not response_text:
            logger.error("Failed to generate response")
            return jsonify({"error": "Failed to generate response"}), 500

        # Save to Firestore if session_id provided
        if session_id and firebase_service.is_available():
            firebase_service.save_message(session_id, "user", user_message)
            firebase_service.save_message(session_id, "assistant", response_text)

        logger.info(f"Chat response generated for user (length: {len(response_text)})")

        return jsonify({
            "response": response_text,
            "country": country if country else None,
            "gemini_available": gemini_service.is_available(),
        }), 200

    except Exception as e:
        logger.error(f"Chat route error: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500


@chat_bp.route("/api/chat/grounded", methods=["POST"])
@limiter.limit(f"{CHAT_REQUESTS_PER_MINUTE}/minute")
def chat_grounded() -> tuple[dict, int]:
    """
    Generate grounded, fact-checked response using Vertex AI Search.
    Includes citations and sources.

    Returns:
        JSON with 'response', 'sources', and 'grounded' fields
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(force=True)
        user_message = _sanitize_input(data.get("message", ""))

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # TODO: Implement Vertex AI grounding when credentials available
        # For now, return standard response
        from services.vertex_service import get_vertex_service

        vertex_service = get_vertex_service()
        result = vertex_service.search_with_grounding(user_message)

        if result.get("error"):
            logger.warning(f"Grounded search unavailable: {result.get('error')}")
            return jsonify({
                "grounded": False,
                "message": result.get("error"),
            }), 503

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Grounded chat error: {e}")
        return jsonify({"error": "Failed to process grounded query"}), 500


@chat_bp.route("/api/chat/history/<session_id>", methods=["GET"])
def get_chat_history(session_id: str) -> tuple[dict, int]:
    """
    Retrieve chat history for a session.

    Args:
        session_id: Unique session identifier

    Returns:
        JSON array of chat messages
    """
    try:
        # Validate session_id
        if not session_id or len(session_id) > 100:
            return jsonify({"error": "Invalid session_id"}), 400

        firebase_service = get_firebase_service()

        if not firebase_service.is_available():
            logger.warning("Firebase service unavailable for history retrieval")
            return jsonify({"error": "Chat history not available"}), 503

        history = firebase_service.get_session_history(session_id, limit=50)

        return jsonify({
            "session_id": session_id,
            "messages": history,
            "count": len(history),
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        return jsonify({"error": "Failed to retrieve chat history"}), 500
