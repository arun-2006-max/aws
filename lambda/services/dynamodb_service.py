"""
DynamoDB data access layer.

Provides CRUD operations for all DynamoDB tables using the
data models in lambda/models/.
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key

from utils.config import Settings
from models.user import User
from models.session import Session
from models.interaction_log import InteractionLog
from models.learning_progress import LearningProgress
from models.knowledge_gap import KnowledgeGap

logger = logging.getLogger(__name__)


class DynamoDBService:
    """Data access layer for all DynamoDB tables."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings.from_env()
        self._resource = boto3.resource(
            "dynamodb", region_name=self._settings.aws_region
        )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _table(self, name: str):
        return self._resource.Table(name)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def save_user(self, user: User) -> None:
        """Persist a User record."""
        is_valid, err = user.validate()
        if not is_valid:
            raise ValueError(f"Invalid user: {err}")
        self._table(self._settings.users_table).put_item(
            Item=user.to_dynamodb_item()
        )

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a User by ID."""
        resp = self._table(self._settings.users_table).get_item(
            Key={"user_id": user_id}
        )
        item = resp.get("Item")
        return User.from_dynamodb_item(item) if item else None

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def save_session(self, session: Session) -> None:
        """Persist a Session record."""
        is_valid, err = session.validate()
        if not is_valid:
            raise ValueError(f"Invalid session: {err}")
        self._table(self._settings.sessions_table).put_item(
            Item=session.to_dynamodb_item()
        )

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a Session by ID."""
        resp = self._table(self._settings.sessions_table).get_item(
            Key={"session_id": session_id}
        )
        item = resp.get("Item")
        return Session.from_dynamodb_item(item) if item else None

    # ------------------------------------------------------------------
    # Interaction Logs
    # ------------------------------------------------------------------

    def save_interaction(self, log: InteractionLog) -> None:
        """Persist an InteractionLog record."""
        is_valid, err = log.validate()
        if not is_valid:
            raise ValueError(f"Invalid interaction log: {err}")
        item = log.to_dynamodb_item()
        # Store timestamp as epoch number for sort key
        item["timestamp"] = int(
            log.timestamp.timestamp()
        )
        self._table(self._settings.interaction_logs_table).put_item(
            Item=item
        )

    def get_user_interactions(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[InteractionLog]:
        """Retrieve recent interactions for a user (newest first)."""
        resp = self._table(self._settings.interaction_logs_table).query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [
            InteractionLog.from_dynamodb_item(item)
            for item in resp.get("Items", [])
        ]

    def update_interaction_feedback(
        self,
        user_id: str,
        timestamp: int,
        rating: int,
    ) -> None:
        """Update the feedback rating on an existing interaction."""
        self._table(self._settings.interaction_logs_table).update_item(
            Key={"user_id": user_id, "timestamp": timestamp},
            UpdateExpression="SET feedback_rating = :r",
            ExpressionAttributeValues={":r": rating},
        )

    # ------------------------------------------------------------------
    # Learning Progress
    # ------------------------------------------------------------------

    def save_learning_progress(self, progress: LearningProgress) -> None:
        """Persist a LearningProgress record."""
        is_valid, err = progress.validate()
        if not is_valid:
            raise ValueError(f"Invalid learning progress: {err}")
        self._table(self._settings.learning_progress_table).put_item(
            Item=progress.to_dynamodb_item()
        )

    def get_learning_progress(
        self, user_id: str
    ) -> list[LearningProgress]:
        """Retrieve all learning progress entries for a user."""
        resp = self._table(self._settings.learning_progress_table).query(
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        return [
            LearningProgress.from_dynamodb_item(item)
            for item in resp.get("Items", [])
        ]

    # ------------------------------------------------------------------
    # Knowledge Gaps
    # ------------------------------------------------------------------

    def save_knowledge_gap(self, gap: KnowledgeGap) -> None:
        """Persist a KnowledgeGap record."""
        is_valid, err = gap.validate()
        if not is_valid:
            raise ValueError(f"Invalid knowledge gap: {err}")
        self._table(self._settings.knowledge_gaps_table).put_item(
            Item=gap.to_dynamodb_item()
        )

    def get_knowledge_gaps(
        self,
        user_id: str,
        resolved: Optional[bool] = None,
    ) -> list[KnowledgeGap]:
        """Retrieve knowledge gaps for a user, optionally filtered."""
        resp = self._table(self._settings.knowledge_gaps_table).query(
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        gaps = [
            KnowledgeGap.from_dynamodb_item(item)
            for item in resp.get("Items", [])
        ]
        if resolved is not None:
            gaps = [g for g in gaps if g.resolved == resolved]
        return gaps

    # ------------------------------------------------------------------
    # Response Cache
    # ------------------------------------------------------------------

    def cache_response(self, query: str, response: dict[str, Any]) -> None:
        """Cache an AI response keyed by query hash."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        ttl = int(time.time()) + self._settings.response_cache_ttl
        self._table(self._settings.response_cache_table).put_item(
            Item={
                "query_hash": query_hash,
                "response": response,
                "ttl": ttl,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def get_cached_response(self, query: str) -> Optional[dict[str, Any]]:
        """Retrieve a cached response for a query, if not expired."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        resp = self._table(self._settings.response_cache_table).get_item(
            Key={"query_hash": query_hash}
        )
        item = resp.get("Item")
        if item and item.get("ttl", 0) > int(time.time()):
            return item.get("response")
        return None
