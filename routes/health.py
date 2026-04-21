"""
Health Check Route
Provides service status endpoint for load balancers and monitoring
"""

import logging
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check() -> tuple[dict, int]:
    """
    Health check endpoint for Cloud Run and monitoring systems.

    Returns:
        JSON response with service status
    """
    return jsonify({
        "status": "ok",
        "service": "VoteSmart AI",
        "version": "1.0.0",
        "component": "api-server",
    }), 200
