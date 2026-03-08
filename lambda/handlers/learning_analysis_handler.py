"""
Learning Analysis handler – POST /learning-analysis

Analyses a user's interaction history to detect knowledge gaps,
then uses Claude Haiku to generate personalised learning suggestions.
"""

import logging
from datetime import datetime

from utils.config import Settings
from utils.response import (
    success_response,
    error_response,
    extract_user_id,
    parse_body,
)
from services.bedrock_service import BedrockService
from services.dynamodb_service import DynamoDBService
from models.knowledge_gap import KnowledgeGap

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_settings = None
_bedrock = None
_db = None

_ANALYSIS_SYSTEM_PROMPT = """You are an expert learning analyst.
Analyse the user's recent questions and identify knowledge gaps.
For each gap, provide:
1. Topic name
2. Confidence score (0.0 to 1.0) indicating how certain you are
3. Two or three actionable learning suggestions

Return your analysis as JSON with this schema:
{
  "gaps": [
    {
      "topic": "string",
      "confidence": 0.0,
      "suggestions": ["string"]
    }
  ],
  "summary": "string"
}
"""


def _init():
    global _settings, _bedrock, _db
    if _settings is None:
        _settings = Settings.from_env()
        _bedrock = BedrockService(_settings)
        _db = DynamoDBService(_settings)


def lambda_handler(event, context):
    """
    Handle POST /learning-analysis requests.

    Optional body:
        { "limit": 20 }
    """
    _init()

    user_id = extract_user_id(event)
    if not user_id:
        return error_response("Unauthorized", 401)

    body = parse_body(event) or {}
    limit = min(int(body.get("limit", 20)), 100)

    # Fetch recent interactions
    interactions = _db.get_user_interactions(user_id, limit=limit)
    if not interactions:
        return success_response({
            "gaps": [],
            "summary": "Not enough interaction data for analysis.",
        })

    # Build prompt from interaction history
    history_lines = [
        f"Q: {i.query}" for i in interactions if i.query
    ]
    history_text = "\n".join(history_lines)
    prompt = (
        f"Here are the user's recent {len(history_lines)} questions:\n"
        f"{history_text}\n\n"
        "Analyse these and identify knowledge gaps."
    )

    # Use Haiku for cost-optimized analysis
    try:
        result = _bedrock.invoke_haiku(
            prompt=prompt,
            system_prompt=_ANALYSIS_SYSTEM_PROMPT,
        )
    except Exception as exc:
        logger.exception("Learning analysis failed")
        return error_response(f"AI service error: {exc}", 502)

    # Persist detected gaps
    import json as _json
    try:
        analysis = _json.loads(result["response"])
        for gap_data in analysis.get("gaps", []):
            gap = KnowledgeGap(
                user_id=user_id,
                topic=gap_data.get("topic", "Unknown"),
                confidence_score=float(gap_data.get("confidence", 0.5)),
                suggestions=gap_data.get("suggestions", []),
                related_queries=[i.interaction_id for i in interactions[:5]],
            )
            _db.save_knowledge_gap(gap)
    except (_json.JSONDecodeError, Exception):
        logger.warning("Could not parse analysis as structured JSON")
        analysis = {"raw_response": result["response"]}

    return success_response({
        "analysis": analysis,
        "model": result["model"],
        "interactions_analysed": len(interactions),
    })
