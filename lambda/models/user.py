"""
User data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re


@dataclass
class User:
    """
    Represents a user in the AI Builder Copilot system.
    
    Attributes:
        user_id: Unique identifier for the user (from Cognito)
        email: User's email address
        created_at: Timestamp when user was created
        last_login: Timestamp of last login
        is_admin: Whether user has admin privileges
    """
    user_id: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_admin: bool = False
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the user data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate user_id
        if not self.user_id or not isinstance(self.user_id, str):
            return False, "user_id must be a non-empty string"
        
        if len(self.user_id) > 128:
            return False, "user_id must not exceed 128 characters"
        
        # Validate email
        if not self.email or not isinstance(self.email, str):
            return False, "email must be a non-empty string"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            return False, "email must be a valid email address"
        
        # Validate timestamps
        if not isinstance(self.created_at, datetime):
            return False, "created_at must be a datetime object"
        
        if self.last_login is not None and not isinstance(self.last_login, datetime):
            return False, "last_login must be a datetime object or None"
        
        # Validate is_admin
        if not isinstance(self.is_admin, bool):
            return False, "is_admin must be a boolean"
        
        return True, None
    
    def to_dynamodb_item(self) -> dict:
        """
        Convert user to DynamoDB item format.
        
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        item = {
            'user_id': self.user_id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_admin': self.is_admin,
        }
        
        if self.last_login:
            item['last_login'] = self.last_login.isoformat()
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'User':
        """
        Create User instance from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            User instance
        """
        return cls(
            user_id=item['user_id'],
            email=item['email'],
            created_at=datetime.fromisoformat(item['created_at']),
            last_login=datetime.fromisoformat(item['last_login']) if 'last_login' in item else None,
            is_admin=item.get('is_admin', False),
        )
