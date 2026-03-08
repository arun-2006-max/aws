"""
Debug Assistant handler – POST /debug-assistant

Accepts code and an error message, uses RAG for relevant docs,
invokes Claude Sonnet for root-cause analysis, and returns a
structured debugging response.
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

_settings = None
_rag = None
_db = None

_DEBUG_SYSTEM_PROMPT = """You are an expert debugging assistant.
Analyse the provided code and error, then respond with a structured
JSON object:

{
  "root_cause": "Clear explanation of what went wrong",
  "fix": "The corrected code or specific changes needed",
  "explanation": "Step-by-step explanation of the fix",
  "prevention_tips": ["Tip 1", "Tip 2"]
}

Use the CONTEXT DOCUMENTS below if they contain relevant information.

CONTEXT DOCUMENTS:
{context}
"""


def _init():
    global _settings, _rag, _db
    if _settings is None:
        _settings = Settings.from_env()
        _rag = RAGService(_settings)
        _db = DynamoDBService(_settings)


def lambda_handler(event, context):
    """
    Handle POST /debug-assistant requests.

    Expected body:
        {
            "code": "def foo():\\n  return bar",
            "error": "NameError: name 'bar' is not defined",
            "language": "python",
            "session_id": "optional"
        }
    """
    _init()

    user_id = extract_user_id(event)
    if not user_id:
        return error_response("Unauthorized", 401)

    body = parse_body(event)
    if not body:
        return error_response("Request body is required")

    code = body.get("code", "").strip()
    error_msg = body.get("error", "").strip()
    language = body.get("language", "unknown")
    session_id = body.get("session_id", "")

    if not code and not error_msg:
        return error_response("At least 'code' or 'error' must be provided")

    # Build debug query for RAG retrieval
    search_query = f"{language} error: {error_msg}" if error_msg else code[:500]

    # Retrieve context from knowledge base
    try:
        context_docs = _rag.retrieve_context(search_query, k=3)
    except Exception:
        logger.warning("Context retrieval failed; proceeding without context")
        context_docs = []

    # Build augmented prompt
    context_text = "\n\n".join(
        f"[Doc {i+1}] {d['text']}" for i, d in enumerate(context_docs)
    ) or "No relevant context documents found."

    system_prompt = _DEBUG_SYSTEM_PROMPT.format(context=context_text)

    user_prompt = f"""Language: {language}

Code:
```
{code}
```

Error:
```
{error_msg}
```

Provide a structured debugging analysis."""

    # Always use Sonnet for debugging (complex reasoning)
    start_ms = int(time.time() * 1000)
    try:
        from services.bedrock_service import BedrockService
        bedrock = BedrockService(_settings)
        result = bedrock.invoke_sonnet(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )
    except Exception as exc:
        logger.exception("Debug analysis failed")
        return error_response(f"AI service error: {exc}", 502)
    latency_ms = int(time.time() * 1000) - start_ms

    # Log interaction
    try:
        log = InteractionLog(
            user_id=user_id,
            session_id=session_id,
            query=f"[DEBUG] {error_msg or code[:200]}",
            response=result["response"],
            model_used=result["model"],
            timestamp=datetime.utcnow(),
            latency_ms=latency_ms,
            token_count=result.get("input_tokens", 0)
            + result.get("output_tokens", 0),
        )
        _db.save_interaction(log)
    except Exception:
        logger.exception("Failed to log debug interaction")

    return success_response({
        "debug_analysis": result["response"],
        "model": result["model"],
        "latency_ms": latency_ms,
        "sources": [
            {"source_key": d["source_key"], "score": d["score"]}
            for d in context_docs
        ],
    })
