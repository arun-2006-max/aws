"""
Session data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Session:
    """
    Represents a user session in the AI Builder Copilot system.
    
    Attributes:
        session_id: Unique identifier for the session
        user_id: ID of the user who owns this session
        started_at: Timestamp when session started
        ended_at: Timestamp when session ended (None if active)
        interaction_count: Number of interactions in this session
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    interaction_count: int = 0
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the session data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate session_id
        if not self.session_id or not isinstance(self.session_id, str):
            return False, "session_id must be a non-empty string"
        
        # Validate user_id
        if not self.user_id or not isinstance(self.user_id, str):
            return False, "user_id must be a non-empty string"
        
        # Validate timestamps
        if not isinstance(self.started_at, datetime):
            return False, "started_at must be a datetime object"
        
        if self.ended_at is not None:
            if not isinstance(self.ended_at, datetime):
                return False, "ended_at must be a datetime object or None"
            
            if self.ended_at < self.started_at:
                return False, "ended_at must be after started_at"
        
        # Validate interaction_count
        if not isinstance(self.interaction_count, int):
            return False, "interaction_count must be an integer"
        
        if self.interaction_count < 0:
            return False, "interaction_count must be non-negative"
        
        return True, None
    
    def is_active(self) -> bool:
        """
        Check if session is currently active.
        
        Returns:
            True if session is active (not ended)
        """
        return self.ended_at is None
    
    def end_session(self) -> None:
        """
        Mark the session as ended.
        """
        self.ended_at = datetime.utcnow()
    
    def to_dynamodb_item(self) -> dict:
        """
        Convert session to DynamoDB item format.
        
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        item = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'started_at': self.started_at.isoformat(),
            'interaction_count': self.interaction_count,
        }
        
        if self.ended_at:
            item['ended_at'] = self.ended_at.isoformat()
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'Session':
        """
        Create Session instance from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            Session instance
        """
        return cls(
            session_id=item['session_id'],
            user_id=item['user_id'],
            started_at=datetime.fromisoformat(item['started_at']),
            ended_at=datetime.fromisoformat(item['ended_at']) if 'ended_at' in item else None,
            interaction_count=item.get('interaction_count', 0),
        )
