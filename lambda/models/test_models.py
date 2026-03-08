"""
Unit tests for data models.
"""

import unittest
from datetime import datetime, timedelta
from models.user import User
from models.session import Session
from models.interaction_log import InteractionLog
from models.learning_progress import LearningProgress
from models.knowledge_gap import KnowledgeGap


class TestUser(unittest.TestCase):
    """Test cases for User model."""
    
    def test_valid_user(self):
        """Test creating a valid user."""
        user = User(
            user_id="user123",
            email="test@example.com"
        )
        is_valid, error = user.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_invalid_email(self):
        """Test user with invalid email."""
        user = User(
            user_id="user123",
            email="invalid-email"
        )
        is_valid, error = user.validate()
        self.assertFalse(is_valid)
        self.assertIn("email", error.lower())
    
    def test_empty_user_id(self):
        """Test user with empty user_id."""
        user = User(
            user_id="",
            email="test@example.com"
        )
        is_valid, error = user.validate()
        self.assertFalse(is_valid)
        self.assertIn("user_id", error.lower())
    
    def test_dynamodb_conversion(self):
        """Test conversion to/from DynamoDB format."""
        user = User(
            user_id="user123",
            email="test@example.com",
            is_admin=True
        )
        
        # Convert to DynamoDB item
        item = user.to_dynamodb_item()
        self.assertEqual(item['user_id'], "user123")
        self.assertEqual(item['email'], "test@example.com")
        self.assertTrue(item['is_admin'])
        
        # Convert back from DynamoDB item
        restored_user = User.from_dynamodb_item(item)
        self.assertEqual(restored_user.user_id, user.user_id)
        self.assertEqual(restored_user.email, user.email)
        self.assertEqual(restored_user.is_admin, user.is_admin)


class TestSession(unittest.TestCase):
    """Test cases for Session model."""
    
    def test_valid_session(self):
        """Test creating a valid session."""
        session = Session(
            user_id="user123"
        )
        is_valid, error = session.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_session_is_active(self):
        """Test session active status."""
        session = Session(user_id="user123")
        self.assertTrue(session.is_active())
        
        session.end_session()
        self.assertFalse(session.is_active())
    
    def test_invalid_ended_at(self):
        """Test session with ended_at before started_at."""
        session = Session(
            user_id="user123",
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow() - timedelta(hours=1)
        )
        is_valid, error = session.validate()
        self.assertFalse(is_valid)
        self.assertIn("ended_at", error.lower())
    
    def test_negative_interaction_count(self):
        """Test session with negative interaction count."""
        session = Session(
            user_id="user123",
            interaction_count=-1
        )
        is_valid, error = session.validate()
        self.assertFalse(is_valid)
        self.assertIn("interaction_count", error.lower())


class TestInteractionLog(unittest.TestCase):
    """Test cases for InteractionLog model."""
    
    def test_valid_interaction_log(self):
        """Test creating a valid interaction log."""
        log = InteractionLog(
            user_id="user123",
            session_id="session456",
            query="What is Python?",
            response="Python is a programming language.",
            model_used="claude-3-haiku"
        )
        is_valid, error = log.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_query_too_long(self):
        """Test interaction log with query exceeding 10000 characters."""
        log = InteractionLog(
            user_id="user123",
            session_id="session456",
            query="x" * 10001,
            response="Response",
            model_used="claude-3-haiku"
        )
        is_valid, error = log.validate()
        self.assertFalse(is_valid)
        self.assertIn("10000", error)
    
    def test_invalid_feedback_rating(self):
        """Test interaction log with invalid feedback rating."""
        log = InteractionLog(
            user_id="user123",
            session_id="session456",
            query="Test query",
            response="Test response",
            model_used="claude-3-haiku",
            feedback_rating=5
        )
        is_valid, error = log.validate()
        self.assertFalse(is_valid)
        self.assertIn("feedback_rating", error.lower())
    
    def test_valid_feedback_ratings(self):
        """Test interaction log with valid feedback ratings."""
        for rating in [-1, 1, None]:
            log = InteractionLog(
                user_id="user123",
                session_id="session456",
                query="Test query",
                response="Test response",
                model_used="claude-3-haiku",
                feedback_rating=rating
            )
            is_valid, error = log.validate()
            self.assertTrue(is_valid, f"Rating {rating} should be valid")


class TestLearningProgress(unittest.TestCase):
    """Test cases for LearningProgress model."""
    
    def test_valid_learning_progress(self):
        """Test creating valid learning progress."""
        progress = LearningProgress(
            user_id="user123"
        )
        is_valid, error = progress.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_add_topic(self):
        """Test adding topics."""
        progress = LearningProgress(user_id="user123")
        progress.add_topic("Python")
        progress.add_topic("AWS")
        
        self.assertEqual(len(progress.topics_covered), 2)
        self.assertIn("Python", progress.topics_covered)
        self.assertIn("AWS", progress.topics_covered)
        
        # Adding duplicate should not increase count
        progress.add_topic("Python")
        self.assertEqual(len(progress.topics_covered), 2)
    
    def test_add_skill(self):
        """Test adding skills."""
        progress = LearningProgress(user_id="user123")
        progress.add_skill("Debugging")
        progress.add_skill("Testing")
        
        self.assertEqual(len(progress.skills_acquired), 2)
        self.assertIn("Debugging", progress.skills_acquired)
    
    def test_increment_questions(self):
        """Test incrementing questions answered."""
        progress = LearningProgress(user_id="user123")
        self.assertEqual(progress.questions_answered, 0)
        
        progress.increment_questions()
        self.assertEqual(progress.questions_answered, 1)
        
        progress.increment_questions(5)
        self.assertEqual(progress.questions_answered, 6)
    
    def test_add_milestone(self):
        """Test adding milestones."""
        progress = LearningProgress(user_id="user123")
        progress.add_milestone("First Question")
        
        self.assertIn("First Question", progress.milestones)
        self.assertIsInstance(progress.milestones["First Question"], str)
    
    def test_negative_questions_answered(self):
        """Test learning progress with negative questions answered."""
        progress = LearningProgress(
            user_id="user123",
            questions_answered=-1
        )
        is_valid, error = progress.validate()
        self.assertFalse(is_valid)
        self.assertIn("questions_answered", error.lower())


class TestKnowledgeGap(unittest.TestCase):
    """Test cases for KnowledgeGap model."""
    
    def test_valid_knowledge_gap(self):
        """Test creating a valid knowledge gap."""
        gap = KnowledgeGap(
            user_id="user123",
            topic="Python Decorators",
            confidence_score=0.85
        )
        is_valid, error = gap.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_invalid_confidence_score(self):
        """Test knowledge gap with invalid confidence score."""
        gap = KnowledgeGap(
            user_id="user123",
            topic="Python",
            confidence_score=1.5
        )
        is_valid, error = gap.validate()
        self.assertFalse(is_valid)
        self.assertIn("confidence_score", error.lower())
    
    def test_mark_resolved(self):
        """Test marking gap as resolved."""
        gap = KnowledgeGap(
            user_id="user123",
            topic="Python"
        )
        self.assertFalse(gap.resolved)
        self.assertIsNone(gap.resolved_at)
        
        gap.mark_resolved()
        self.assertTrue(gap.resolved)
        self.assertIsNotNone(gap.resolved_at)
    
    def test_add_suggestion(self):
        """Test adding suggestions."""
        gap = KnowledgeGap(
            user_id="user123",
            topic="Python"
        )
        gap.add_suggestion("Read Python documentation")
        gap.add_suggestion("Practice with examples")
        
        self.assertEqual(len(gap.suggestions), 2)
        self.assertIn("Read Python documentation", gap.suggestions)
        
        # Adding duplicate should not increase count
        gap.add_suggestion("Read Python documentation")
        self.assertEqual(len(gap.suggestions), 2)
    
    def test_add_related_query(self):
        """Test adding related queries."""
        gap = KnowledgeGap(
            user_id="user123",
            topic="Python"
        )
        gap.add_related_query("query1")
        gap.add_related_query("query2")
        
        self.assertEqual(len(gap.related_queries), 2)
        self.assertIn("query1", gap.related_queries)
    
    def test_resolved_without_timestamp(self):
        """Test validation fails when resolved is True but resolved_at is None."""
        gap = KnowledgeGap(
            user_id="user123",
            topic="Python",
            resolved=True,
            resolved_at=None
        )
        is_valid, error = gap.validate()
        self.assertFalse(is_valid)
        self.assertIn("resolved_at", error.lower())


if __name__ == '__main__':
    unittest.main()
