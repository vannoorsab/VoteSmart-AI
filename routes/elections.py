"""
Election Data Routes
Provides endpoints for election system information and timelines
"""

import json
import logging
from typing import Optional
from flask import Blueprint, jsonify, current_app
from config import ELECTIONS_DATA_FILE, GLOSSARY_DATA_FILE, ALLOWED_COUNTRIES

logger = logging.getLogger(__name__)

elections_bp = Blueprint("elections", __name__)

# Cache for elections data
_elections_cache: Optional[dict] = None
_glossary_cache: Optional[dict] = None


def _load_elections_data() -> dict:
    """Load elections data from JSON file."""
    global _elections_cache
    if _elections_cache is not None:
        return _elections_cache

    try:
        with open(ELECTIONS_DATA_FILE, "r", encoding="utf-8") as f:
            _elections_cache = json.load(f)
        logger.info(f"Loaded elections data with {len(_elections_cache)} countries")
        return _elections_cache
    except Exception as e:
        logger.error(f"Failed to load elections data: {e}")
        return {}


def _load_glossary_data() -> dict:
    """Load glossary data from JSON file."""
    global _glossary_cache
    if _glossary_cache is not None:
        return _glossary_cache

    try:
        with open(GLOSSARY_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _glossary_cache = {term["term"].lower(): term for term in data.get("glossary", [])}
        logger.info(f"Loaded glossary with {len(_glossary_cache)} terms")
        return _glossary_cache
    except Exception as e:
        logger.error(f"Failed to load glossary data: {e}")
        return {}


@elections_bp.route("/api/elections", methods=["GET"])
def get_all_elections() -> tuple[dict, int]:
    """
    Get summary of all supported countries.

    Returns:
        JSON with country summaries: name, flag, system, color, voters
    """
    try:
        data = _load_elections_data()
        summary = {}

        for country_id, country_data in data.items():
            summary[country_id] = {
                "name": country_data.get("name"),
                "flag": country_data.get("flag"),
                "system": country_data.get("system"),
                "color": country_data.get("color"),
                "voters": country_data.get("voters"),
                "body": country_data.get("body"),
            }

        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Error fetching elections: {e}")
        return jsonify({"error": "Failed to fetch elections data"}), 500


@elections_bp.route("/api/elections/<country_id>", methods=["GET"])
def get_election_details(country_id: str) -> tuple[dict, int]:
    """
    Get full election details for a country.

    Args:
        country_id: Country identifier (india, usa, uk, eu, brazil)

    Returns:
        JSON with complete election data including timeline and voting steps
    """
    country_id = country_id.lower()

    if country_id not in ALLOWED_COUNTRIES:
        logger.warning(f"Invalid country requested: {country_id}")
        return jsonify({"error": "Country not found"}), 404

    try:
        data = _load_elections_data()
        country_data = data.get(country_id)

        if not country_data:
            return jsonify({"error": "Country data not found"}), 404

        return jsonify(country_data), 200
    except Exception as e:
        logger.error(f"Error fetching election details for {country_id}: {e}")
        return jsonify({"error": "Failed to fetch election data"}), 500


@elections_bp.route("/api/elections/<country_id>/timeline", methods=["GET"])
def get_election_timeline(country_id: str) -> tuple[dict, int]:
    """
    Get election timeline for a country.

    Args:
        country_id: Country identifier

    Returns:
        JSON array of timeline phases with dates and descriptions
    """
    country_id = country_id.lower()

    if country_id not in ALLOWED_COUNTRIES:
        return jsonify({"error": "Country not found"}), 404

    try:
        data = _load_elections_data()
        country_data = data.get(country_id, {})
        timeline = country_data.get("timeline", [])

        if not timeline:
            logger.warning(f"No timeline found for {country_id}")
            return jsonify({"error": "Timeline not found"}), 404

        return jsonify({
            "country": country_id,
            "country_name": country_data.get("name"),
            "timeline": timeline,
        }), 200
    except Exception as e:
        logger.error(f"Error fetching timeline for {country_id}: {e}")
        return jsonify({"error": "Failed to fetch timeline"}), 500


@elections_bp.route("/api/elections/<country_id>/voting-steps", methods=["GET"])
def get_voting_steps(country_id: str) -> tuple[dict, int]:
    """
    Get how-to-vote steps for a country.

    Args:
        country_id: Country identifier

    Returns:
        JSON array of voting steps with icons and details
    """
    country_id = country_id.lower()

    if country_id not in ALLOWED_COUNTRIES:
        return jsonify({"error": "Country not found"}), 404

    try:
        data = _load_elections_data()
        country_data = data.get(country_id, {})
        steps = country_data.get("steps", [])

        if not steps:
            logger.warning(f"No voting steps found for {country_id}")
            return jsonify({"error": "Voting steps not found"}), 404

        return jsonify({
            "country": country_id,
            "country_name": country_data.get("name"),
            "steps": steps,
        }), 200
    except Exception as e:
        logger.error(f"Error fetching voting steps for {country_id}: {e}")
        return jsonify({"error": "Failed to fetch voting steps"}), 500


@elections_bp.route("/api/glossary", methods=["GET"])
def get_glossary() -> tuple[dict, int]:
    """
    Get election terminology glossary.

    Returns:
        JSON array of terms and definitions
    """
    try:
        with open(GLOSSARY_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error fetching glossary: {e}")
        return jsonify({"error": "Failed to fetch glossary"}), 500


@elections_bp.route("/api/glossary/<term>", methods=["GET"])
def get_glossary_term(term: str) -> tuple[dict, int]:
    """
    Get definition for a specific glossary term.

    Args:
        term: Term to look up

    Returns:
        JSON with term definition and examples
    """
    term_lower = term.lower()

    try:
        glossary = _load_glossary_data()

        if term_lower not in glossary:
            logger.warning(f"Glossary term not found: {term}")
            return jsonify({"error": "Term not found"}), 404

        return jsonify(glossary[term_lower]), 200
    except Exception as e:
        logger.error(f"Error fetching glossary term {term}: {e}")
        return jsonify({"error": "Failed to fetch term"}), 500
