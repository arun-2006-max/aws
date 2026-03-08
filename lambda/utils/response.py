"""
Standardized API Gateway response helpers.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def success_response(body: Any, status_code: int = 200) -> dict:
    """
    Build a successful API Gateway proxy response.

    Args:
        body: Response body (will be JSON-serialized).
        status_code: HTTP status code (default 200).

    Returns:
        API Gateway proxy response dict.
    """
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
) -> dict:
    """
    Build an error API Gateway proxy response.

    Args:
        message: Human-readable error message.
        status_code: HTTP status code (default 400).
        error_code: Optional machine-readable error code.

    Returns:
        API Gateway proxy response dict.
    """
    body: dict[str, Any] = {"error": message}
    if error_code:
        body["error_code"] = error_code

    logger.warning("Error response %d: %s", status_code, message)
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def extract_user_id(event: dict) -> Optional[str]:
    """
    Extract the authenticated user ID from an API Gateway event.

    The user ID is sourced from the Cognito authorizer claims
    embedded in the request context.

    Args:
        event: API Gateway proxy event.

    Returns:
        User ID string, or None if not found.
    """
    try:
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("claims", {})
        )
        return claims.get("sub") or claims.get("cognito:username")
    except (AttributeError, TypeError):
        logger.error("Failed to extract user ID from event")
        return None


def parse_body(event: dict) -> Optional[dict]:
    """
    Parse the JSON body from an API Gateway event.

    Args:
        event: API Gateway proxy event.

    Returns:
        Parsed body dict, or None on failure.
    """
    try:
        body = event.get("body")
        if body is None:
            return None
        if isinstance(body, str):
            return json.loads(body)
        return body
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to parse request body: %s", exc)
        return None
