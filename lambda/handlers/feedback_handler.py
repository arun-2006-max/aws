"""
Feedback handler – POST /store-feedback

Stores user feedback (thumbs up/down) for a specific interaction.
"""

import logging

from utils.config import Settings
from utils.response import (
    success_response,
    error_response,
    extract_user_id,
    parse_body,
)
from services.dynamodb_service import DynamoDBService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_settings = None
_db = None


def _init():
    global _settings, _db
    if _settings is None:
        _settings = Settings.from_env()
        _db = DynamoDBService(_settings)


def lambda_handler(event, context):
    """
    Handle POST /store-feedback requests.

    Expected body:
        {
            "interaction_timestamp": 1709900000,
            "rating": 1          // 1 = positive, -1 = negative
        }
    """
    _init()

    user_id = extract_user_id(event)
    if not user_id:
        return error_response("Unauthorized", 401)

    body = parse_body(event)
    if not body:
        return error_response("Request body is required")

    timestamp = body.get("interaction_timestamp")
    rating = body.get("rating")

    if timestamp is None:
        return error_response("'interaction_timestamp' is required")

    if rating not in (1, -1):
        return error_response("'rating' must be 1 (positive) or -1 (negative)")

    try:
        _db.update_interaction_feedback(
            user_id=user_id,
            timestamp=int(timestamp),
            rating=int(rating),
        )
    except Exception as exc:
        logger.exception("Failed to store feedback")
        return error_response(f"Failed to store feedback: {exc}", 500)

    return success_response({
        "message": "Feedback stored successfully",
        "rating": rating,
    })
