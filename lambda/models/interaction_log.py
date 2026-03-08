"""
InteractionLog data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class InteractionLog:
    """
    Represents a logged interaction between user and AI.
    
    Attributes:
        interaction_id: Unique identifier for the interaction
        user_id: ID of the user
        session_id: ID of the session this interaction belongs to
        query: User's query text
        response: AI's response text
        model_used: Name of the Bedrock model used
        timestamp: When the interaction occurred
        latency_ms: Response latency in milliseconds
        token_count: Number of tokens used
        feedback_rating: User feedback (1 for positive, -1 for negative, None if no feedback)
    """
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    session_id: str = ""
    query: str = ""
    response: str = ""
    model_used: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: int = 0
    token_count: int = 0
    feedback_rating: Optional[int] = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the interaction log data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate interaction_id
        if not self.interaction_id or not isinstance(self.interaction_id, str):
            return False, "interaction_id must be a non-empty string"
        
        # Validate user_id
        if not self.user_id or not isinstance(self.user_id, str):
            return False, "user_id must be a non-empty string"
        
        # Validate session_id
        if not self.session_id or not isinstance(self.session_id, str):
            return False, "session_id must be a non-empty string"
        
        # Validate query
        if not self.query or not isinstance(self.query, str):
            return False, "query must be a non-empty string"
        
        if len(self.query) > 10000:
            return False, "query must not exceed 10000 characters"
        
        # Validate response
        if not isinstance(self.response, str):
            return False, "response must be a string"
        
        # Validate model_used
        if not self.model_used or not isinstance(self.model_used, str):
            return False, "model_used must be a non-empty string"
        
        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            return False, "timestamp must be a datetime object"
        
        # Validate latency_ms
        if not isinstance(self.latency_ms, int):
            return False, "latency_ms must be an integer"
        
        if self.latency_ms < 0:
            return False, "latency_ms must be non-negative"
        
        # Validate token_count
        if not isinstance(self.token_count, int):
            return False, "token_count must be an integer"
        
        if self.token_count < 0:
            return False, "token_count must be non-negative"
        
        # Validate feedback_rating
        if self.feedback_rating is not None:
            if not isinstance(self.feedback_rating, int):
                return False, "feedback_rating must be an integer or None"
            
            if self.feedback_rating not in [-1, 1]:
                return False, "feedback_rating must be -1, 1, or None"
        
        return True, None
    
    def to_dynamodb_item(self) -> dict:
        """
        Convert interaction log to DynamoDB item format.
        
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        item = {
            'interaction_id': self.interaction_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'query': self.query,
            'response': self.response,
            'model_used': self.model_used,
            'timestamp': self.timestamp.isoformat(),
            'latency_ms': self.latency_ms,
            'token_count': self.token_count,
        }
        
        if self.feedback_rating is not None:
            item['feedback_rating'] = self.feedback_rating
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'InteractionLog':
        """
        Create InteractionLog instance from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            InteractionLog instance
        """
        return cls(
            interaction_id=item['interaction_id'],
            user_id=item['user_id'],
            session_id=item['session_id'],
            query=item['query'],
            response=item['response'],
            model_used=item['model_used'],
            timestamp=datetime.fromisoformat(item['timestamp']),
            latency_ms=item.get('latency_ms', 0),
            token_count=item.get('token_count', 0),
            feedback_rating=item.get('feedback_rating'),
        )
