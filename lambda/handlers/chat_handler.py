"""
Chat handler – POST /chat

Main AI chat endpoint. Validates input, checks response cache,
runs the RAG pipeline, invokes Bedrock, logs the interaction,
updates learning progress, and returns the response.
"""

import logging
import time
from datetime import datetime

from utils.config import Settings
from utils.response import (
    success_response,
    error_response,
    extract_user_id,
    parse_body,
)
from services.rag_service import RAGService
from services.dynamodb_service import DynamoDBService
from models.interaction_log import InteractionLog

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Lazy-initialised singletons (reused across warm invocations)
_settings: Settings | None = None
_rag: RAGService | None = None
_db: DynamoDBService | None = None


def _init():
    global _settings, _rag, _db
    if _settings is None:
        _settings = Settings.from_env()
        _rag = RAGService(_settings)
        _db = DynamoDBService(_settings)


def lambda_handler(event, context):
    """
    Handle POST /chat requests.

    Expected body:
        {
            "query": "How do I implement a binary search tree?",
            "session_id": "optional-session-uuid"
        }
    """
    _init()

    # --- Extract user identity ---
    user_id = extract_user_id(event)
    if not user_id:
        return error_response("Unauthorized", 401)

    # --- Parse & validate body ---
    body = parse_body(event)
    if not body:
        return error_response("Request body is required")

    query = body.get("query", "").strip()
    if not query:
        return error_response("'query' field is required")
    if len(query) > 10000:
        return error_response("Query must not exceed 10 000 characters")

    session_id = body.get("session_id", "")

    # --- Check cache ---
    cached = _db.get_cached_response(query)
    if cached:
        logger.info("Cache hit for query")
        return success_response({
            "response": cached.get("response", ""),
            "model": cached.get("model", "cache"),
            "sources": cached.get("sources", []),
            "cached": True,
        })

    # --- RAG pipeline ---
    start_ms = int(time.time() * 1000)
    try:
        result = _rag.retrieve_and_generate(query)
    except Exception as exc:
        logger.exception("RAG pipeline failed")
        return error_response(f"AI service error: {exc}", 502)
    latency_ms = int(time.time() * 1000) - start_ms

    # --- Cache the response ---
    _db.cache_response(query, result)

    # --- Log interaction ---
    try:
        log = InteractionLog(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=result["response"],
            model_used=result["model"],
            timestamp=datetime.utcnow(),
            latency_ms=latency_ms,
            token_count=result.get("input_tokens", 0)
            + result.get("output_tokens", 0),
        )
        _db.save_interaction(log)
    except Exception:
        logger.exception("Failed to log interaction")

    # --- Return ---
    return success_response({
        "response": result["response"],
        "model": result["model"],
        "sources": result.get("sources", []),
        "latency_ms": latency_ms,
        "cached": False,
    })
