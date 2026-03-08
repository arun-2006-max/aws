"""
User Progress handler – GET /user-progress

Retrieves a user's learning progress, knowledge gaps,
interaction statistics, and milestones from DynamoDB.
"""

import logging

from utils.config import Settings
from utils.response import (
    success_response,
    error_response,
    extract_user_id,
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
    Handle GET /user-progress requests.

    Query params (optional):
        ?include_resolved=true   – include resolved knowledge gaps
    """
    _init()

    user_id = extract_user_id(event)
    if not user_id:
        return error_response("Unauthorized", 401)

    params = event.get("queryStringParameters") or {}
    include_resolved = params.get("include_resolved", "false").lower() == "true"

    # Fetch learning progress
    progress_records = _db.get_learning_progress(user_id)

    # Aggregate across all topic records
    all_topics: list[str] = []
    total_questions = 0
    all_skills: list[str] = []
    all_milestones: dict[str, str] = {}
    for p in progress_records:
        all_topics.extend(p.topics_covered)
        total_questions += p.questions_answered
        all_skills.extend(p.skills_acquired)
        all_milestones.update(p.milestones)

    # Fetch knowledge gaps
    if include_resolved:
        gaps = _db.get_knowledge_gaps(user_id)
    else:
        gaps = _db.get_knowledge_gaps(user_id, resolved=False)

    # Recent interactions count
    recent = _db.get_user_interactions(user_id, limit=100)

    return success_response({
        "user_id": user_id,
        "progress": {
            "topics_covered": list(set(all_topics)),
            "total_topics": len(set(all_topics)),
            "questions_answered": total_questions,
            "skills_acquired": list(set(all_skills)),
            "total_skills": len(set(all_skills)),
            "milestones": all_milestones,
        },
        "knowledge_gaps": [
            {
                "gap_id": g.gap_id,
                "topic": g.topic,
                "confidence_score": g.confidence_score,
                "suggestions": g.suggestions,
                "resolved": g.resolved,
                "detected_at": g.detected_at.isoformat(),
            }
            for g in gaps
        ],
        "interaction_stats": {
            "total_recent": len(recent),
        },
    })
