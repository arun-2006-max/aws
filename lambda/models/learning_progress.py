"""
LearningProgress data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class LearningProgress:
    """
    Represents a user's learning progress in the AI Builder Copilot system.
    
    Attributes:
        user_id: ID of the user
        topics_covered: List of topics the user has covered
        questions_answered: Total number of questions answered
        skills_acquired: List of skills the user has acquired
        milestones: Dictionary of milestone achievements with timestamps
        last_updated: Timestamp of last progress update
    """
    user_id: str = ""
    topics_covered: List[str] = field(default_factory=list)
    questions_answered: int = 0
    skills_acquired: List[str] = field(default_factory=list)
    milestones: Dict[str, str] = field(default_factory=dict)  # milestone_name -> timestamp
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the learning progress data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate user_id
        if not self.user_id or not isinstance(self.user_id, str):
            return False, "user_id must be a non-empty string"
        
        # Validate topics_covered
        if not isinstance(self.topics_covered, list):
            return False, "topics_covered must be a list"
        
        for topic in self.topics_covered:
            if not isinstance(topic, str):
                return False, "all topics in topics_covered must be strings"
        
        # Validate questions_answered
        if not isinstance(self.questions_answered, int):
            return False, "questions_answered must be an integer"
        
        if self.questions_answered < 0:
            return False, "questions_answered must be non-negative"
        
        # Validate skills_acquired
        if not isinstance(self.skills_acquired, list):
            return False, "skills_acquired must be a list"
        
        for skill in self.skills_acquired:
            if not isinstance(skill, str):
                return False, "all skills in skills_acquired must be strings"
        
        # Validate milestones
        if not isinstance(self.milestones, dict):
            return False, "milestones must be a dictionary"
        
        for key, value in self.milestones.items():
            if not isinstance(key, str):
                return False, "all milestone keys must be strings"
            if not isinstance(value, str):
                return False, "all milestone values must be strings"
        
        # Validate last_updated
        if not isinstance(self.last_updated, datetime):
            return False, "last_updated must be a datetime object"
        
        return True, None
    
    def add_topic(self, topic: str) -> None:
        """
        Add a new topic to topics covered.
        
        Args:
            topic: Topic name to add
        """
        if topic and topic not in self.topics_covered:
            self.topics_covered.append(topic)
            self.last_updated = datetime.utcnow()
    
    def add_skill(self, skill: str) -> None:
        """
        Add a new skill to skills acquired.
        
        Args:
            skill: Skill name to add
        """
        if skill and skill not in self.skills_acquired:
            self.skills_acquired.append(skill)
            self.last_updated = datetime.utcnow()
    
    def increment_questions(self, count: int = 1) -> None:
        """
        Increment the questions answered counter.
        
        Args:
            count: Number to increment by (default 1)
        """
        if count > 0:
            self.questions_answered += count
            self.last_updated = datetime.utcnow()
    
    def add_milestone(self, milestone_name: str) -> None:
        """
        Record a milestone achievement.
        
        Args:
            milestone_name: Name of the milestone achieved
        """
        if milestone_name:
            self.milestones[milestone_name] = datetime.utcnow().isoformat()
            self.last_updated = datetime.utcnow()
    
    def to_dynamodb_item(self) -> dict:
        """
        Convert learning progress to DynamoDB item format.
        
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        return {
            'user_id': self.user_id,
            'topics_covered': self.topics_covered,
            'questions_answered': self.questions_answered,
            'skills_acquired': self.skills_acquired,
            'milestones': self.milestones,
            'last_updated': self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'LearningProgress':
        """
        Create LearningProgress instance from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            LearningProgress instance
        """
        return cls(
            user_id=item['user_id'],
            topics_covered=item.get('topics_covered', []),
            questions_answered=item.get('questions_answered', 0),
            skills_acquired=item.get('skills_acquired', []),
            milestones=item.get('milestones', {}),
            last_updated=datetime.fromisoformat(item['last_updated']),
        )
