"""
Translation Route
Handles text translation using Google Cloud Translate
"""

import logging
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach
from config import (
    MAX_TEXT_TRANSLATION_LENGTH,
    TRANSLATE_REQUESTS_PER_MINUTE,
)
from services.translate_service import get_translate_service

logger = logging.getLogger(__name__)

translate_bp = Blueprint("translate", __name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def _sanitize_text(text: str, max_length: int = MAX_TEXT_TRANSLATION_LENGTH) -> str:
    """
    Sanitize text for translation.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text or empty string if invalid
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()

    if len(text) == 0 or len(text) > max_length:
        return ""

    # Use bleach to remove HTML/scripts
    text = bleach.clean(text, tags=[], strip=True)

    return text


@translate_bp.route("/api/translate", methods=["POST"])
@limiter.limit(f"{TRANSLATE_REQUESTS_PER_MINUTE}/minute")
def translate_text() -> tuple[dict, int]:
    """
    Translate text to target language.

    Request body:
    {
        "text": "Text to translate",
        "target_language": "es",  # e.g., es, fr, hi, ta, de, pt
        "source_language": "en"   # optional
    }

    Returns:
        JSON with translated_text, source_language, target_language
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(force=True)
        text = _sanitize_text(data.get("text", ""))
        target_lang = data.get("target_language", "").lower()
        source_lang = data.get("source_language", "").lower() if data.get("source_language") else None

        if not text:
            logger.warning("Empty text provided for translation")
            return jsonify({"error": "Text is required (1-5000 characters)"}), 400

        if not target_lang or len(target_lang) != 2:
            logger.warning(f"Invalid target language: {target_lang}")
            return jsonify({"error": "Valid target_language required (e.g., 'es', 'fr', 'hi')"}), 400

        # Get translation service
        translate_service = get_translate_service()

        if not translate_service.is_available():
            logger.warning("Translation service unavailable")
            return jsonify({
                "error": "Translation service not available",
                "text": text,  # Return original text
            }), 503

        # Translate
        result = translate_service.translate_text(
            text=text,
            target_language=target_lang,
            source_language=source_lang,
        )

        if result.get("error"):
            logger.warning(f"Translation error: {result.get('error')}")
            return jsonify(result), 400

        logger.info(
            f"Translation completed: {result.get('source_language')} "
            f"-> {result.get('target_language')}"
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Translation route error: {e}")
        return jsonify({"error": "Failed to translate text"}), 500


@translate_bp.route("/api/translate/detect", methods=["POST"])
@limiter.limit(f"{TRANSLATE_REQUESTS_PER_MINUTE}/minute")
def detect_language() -> tuple[dict, int]:
    """
    Detect language of given text.

    Request body:
    {
        "text": "Text to detect language for"
    }

    Returns:
        JSON with detected_language code
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(force=True)
        text = _sanitize_text(data.get("text", ""))

        if not text:
            return jsonify({"error": "Text is required"}), 400

        translate_service = get_translate_service()

        if not translate_service.is_available():
            logger.warning("Translation service unavailable for language detection")
            return jsonify({"error": "Translation service not available"}), 503

        detected_lang = translate_service.detect_language(text)

        return jsonify({
            "text": text,
            "detected_language": detected_lang,
        }), 200

    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return jsonify({"error": "Failed to detect language"}), 500


@translate_bp.route("/api/languages", methods=["GET"])
def get_supported_languages() -> tuple[dict, int]:
    """
    Get list of supported languages for translation.

    Returns:
        JSON with list of language codes
    """
    try:
        translate_service = get_translate_service()
        languages = translate_service.get_supported_languages()

        return jsonify({
            "supported_languages": languages,
            "count": len(languages),
        }), 200

    except Exception as e:
        logger.error(f"Error fetching supported languages: {e}")
        return jsonify({"error": "Failed to fetch language list"}), 500
