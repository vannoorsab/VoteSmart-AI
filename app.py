"""
VoteSmart AI - Global Election Education Platform
Production-grade Flask application with Google AI integration
"""

import os
import logging
from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import config
from routes.elections import elections_bp
from routes.chat import chat_bp
from routes.translate import translate_bp
from routes.health import health_bp

# ──────────────────────────────────────────────
# LOGGING CONFIGURATION
# ──────────────────────────────────────────────

logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# APP FACTORY
# ──────────────────────────────────────────────

def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        Configured Flask app instance
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # ── Configuration ──
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["TESTING"] = config.TESTING

    # ── Rate Limiting ──
    if config.RATELIMIT_ENABLED:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=config.RATELIMIT_STORAGE_URI,
        )
        logger.info("Rate limiting enabled")

    # ── Security Headers ──
    @app.after_request
    def apply_security_headers(response):
        """Apply security headers to all responses."""
        # Prevent content-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = config.CSP_HEADER

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        return response

    # ── Routes ──
    @app.route("/")
    def index():
        """Render main SPA template."""
        from routes.elections import _load_elections_data

        elections_data = _load_elections_data()
        countries = {}
        for key, data in elections_data.items():
            countries[key] = {
                "name": data.get("name"),
                "flag": data.get("flag"),
                "system": data.get("system"),
                "color": data.get("color"),
            }

        return render_template("index.html", countries=countries)

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(elections_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(translate_bp)

    logger.info("Flask application created and configured")
    return app


# ──────────────────────────────────────────────
# APP INSTANCE & ENTRY POINT
# ──────────────────────────────────────────────

app = create_app()


# ── LEGACY DATA (kept for backwards compatibility with existing tests) ──
# Load from new locations
from routes.elections import _load_elections_data
ELECTION_DATA = _load_elections_data()


def fallback_response(message: str) -> str:
    """
    Provide fallback responses when Gemini is unavailable.
    (Kept for backwards compatibility with existing tests)
    """
    msg = message.lower()
    if "india" in msg:
        return "🇮🇳 India uses a Parliamentary system. The Election Commission of India (ECI) oversees elections. Citizens vote for 543 Lok Sabha seats every 5 years using Electronic Voting Machines (EVMs). The party or coalition with 272+ seats forms the government."
    elif "usa" in msg or "america" in msg or "united states" in msg:
        return "🇺🇸 The USA holds Presidential elections every 4 years. Citizens don't directly elect the President — they vote for Electors who form the Electoral College (538 total). A candidate needs 270 electoral votes to win."
    elif "uk" in msg or "britain" in msg or "england" in msg:
        return "🇬🇧 The UK uses First Past the Post voting. Citizens elect 650 MPs to the House of Commons. The leader of the party with most MPs becomes Prime Minister, invited by the Monarch."
    elif "brazil" in msg:
        return "🇧🇷 Brazil has compulsory voting for ages 18–70. The President is elected via a two-round majority system. Brazil pioneered fully electronic voting in 1996 — one of the world's most advanced systems."
    elif "eu" in msg or "europe" in msg:
        return "🇪🇺 EU citizens elect 720 Members of European Parliament (MEPs) every 5 years. Each of the 27 member states uses proportional representation. The Parliament co-legislates EU law."
    return "I'm VoteSmart AI, your election education guide! Ask me about voting systems, timelines, or the election process in India, USA, UK, EU, Brazil, and more. 🗳️"


if __name__ == "__main__":
    port = config.PORT
    logger.info(f"Starting VoteSmart AI server on {config.HOST}:{port}")
    app.run(host=config.HOST, port=port, debug=config.DEBUG)
