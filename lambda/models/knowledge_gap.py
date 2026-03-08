"""
KnowledgeGap data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class KnowledgeGap:
    """
    Represents an identified knowledge gap for a user.
    
    Attributes:
        gap_id: Unique identifier for the knowledge gap
        user_id: ID of the user
        topic: Topic where the gap was identified
        detected_at: Timestamp when gap was detected
        confidence_score: Confidence score for the detection (0.0 to 1.0)
        related_queries: List of query IDs that led to this detection
        suggestions: List of learning suggestions to address the gap
        resolved: Whether the gap has been resolved
        resolved_at: Timestamp when gap was resolved (None if not resolved)
    """
    gap_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    topic: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0
    related_queries: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the knowledge gap data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate gap_id
        if not self.gap_id or not isinstance(self.gap_id, str):
            return False, "gap_id must be a non-empty string"
        
        # Validate user_id
        if not self.user_id or not isinstance(self.user_id, str):
            return False, "user_id must be a non-empty string"
        
        # Validate topic
        if not self.topic or not isinstance(self.topic, str):
            return False, "topic must be a non-empty string"
        
        # Validate detected_at
        if not isinstance(self.detected_at, datetime):
            return False, "detected_at must be a datetime object"
        
        # Validate confidence_score
        if not isinstance(self.confidence_score, (int, float)):
            return False, "confidence_score must be a number"
        
        if not 0.0 <= self.confidence_score <= 1.0:
            return False, "confidence_score must be between 0.0 and 1.0"
        
        # Validate related_queries
        if not isinstance(self.related_queries, list):
            return False, "related_queries must be a list"
        
        for query_id in self.related_queries:
            if not isinstance(query_id, str):
                return False, "all query IDs in related_queries must be strings"
        
        # Validate suggestions
        if not isinstance(self.suggestions, list):
            return False, "suggestions must be a list"
        
        for suggestion in self.suggestions:
            if not isinstance(suggestion, str):
                return False, "all suggestions must be strings"
        
        # Validate resolved
        if not isinstance(self.resolved, bool):
            return False, "resolved must be a boolean"
        
        # Validate resolved_at
        if self.resolved_at is not None:
            if not isinstance(self.resolved_at, datetime):
                return False, "resolved_at must be a datetime object or None"
            
            if self.resolved_at < self.detected_at:
                return False, "resolved_at must be after detected_at"
        
        # Logical validation: if resolved is True, resolved_at should be set
        if self.resolved and self.resolved_at is None:
            return False, "resolved_at must be set when resolved is True"
        
        return True, None
    
    def mark_resolved(self) -> None:
        """
        Mark the knowledge gap as resolved.
        """
        self.resolved = True
        self.resolved_at = datetime.utcnow()
    
    def add_suggestion(self, suggestion: str) -> None:
        """
        Add a learning suggestion to address the gap.
        
        Args:
            suggestion: Learning suggestion text
        """
        if suggestion and suggestion not in self.suggestions:
            self.suggestions.append(suggestion)
    
    def add_related_query(self, query_id: str) -> None:
        """
        Add a related query ID that contributed to this gap detection.
        
        Args:
            query_id: ID of the related query
        """
        if query_id and query_id not in self.related_queries:
            self.related_queries.append(query_id)
    
    def to_dynamodb_item(self) -> dict:
        """
        Convert knowledge gap to DynamoDB item format.
        
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        item = {
            'gap_id': self.gap_id,
            'user_id': self.user_id,
            'topic': self.topic,
            'detected_at': self.detected_at.isoformat(),
            'confidence_score': self.confidence_score,
            'related_queries': self.related_queries,
            'suggestions': self.suggestions,
            'resolved': self.resolved,
        }
        
        if self.resolved_at:
            item['resolved_at'] = self.resolved_at.isoformat()
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'KnowledgeGap':
        """
        Create KnowledgeGap instance from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            KnowledgeGap instance
        """
        return cls(
            gap_id=item['gap_id'],
            user_id=item['user_id'],
            topic=item['topic'],
            detected_at=datetime.fromisoformat(item['detected_at']),
            confidence_score=item.get('confidence_score', 0.0),
            related_queries=item.get('related_queries', []),
            suggestions=item.get('suggestions', []),
            resolved=item.get('resolved', False),
            resolved_at=datetime.fromisoformat(item['resolved_at']) if 'resolved_at' in item else None,
        )
