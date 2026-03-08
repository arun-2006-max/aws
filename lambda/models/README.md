# Data Models

This directory contains the Python data model classes for the AI Builder Copilot system.

## Models

### User
Represents a user in the system with authentication and profile information.

**Attributes:**
- `user_id`: Unique identifier (from Cognito)
- `email`: User's email address
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp
- `is_admin`: Admin privileges flag

**Methods:**
- `validate()`: Validates all user data
- `to_dynamodb_item()`: Converts to DynamoDB format
- `from_dynamodb_item()`: Creates instance from DynamoDB data

### Session
Represents a user session tracking interactions.

**Attributes:**
- `session_id`: Unique session identifier
- `user_id`: Owner user ID
- `started_at`: Session start timestamp
- `ended_at`: Session end timestamp (None if active)
- `interaction_count`: Number of interactions in session

**Methods:**
- `validate()`: Validates session data
- `is_active()`: Checks if session is active
- `end_session()`: Marks session as ended
- `to_dynamodb_item()`: Converts to DynamoDB format
- `from_dynamodb_item()`: Creates instance from DynamoDB data

### InteractionLog
Records user-AI interactions with metadata.

**Attributes:**
- `interaction_id`: Unique interaction identifier
- `user_id`: User who made the query
- `session_id`: Associated session
- `query`: User's query text (max 10000 chars)
- `response`: AI's response text
- `model_used`: Bedrock model name
- `timestamp`: Interaction timestamp
- `latency_ms`: Response latency in milliseconds
- `token_count`: Tokens used
- `feedback_rating`: User feedback (-1, 1, or None)

**Methods:**
- `validate()`: Validates interaction data
- `to_dynamodb_item()`: Converts to DynamoDB format
- `from_dynamodb_item()`: Creates instance from DynamoDB data

### LearningProgress
Tracks user's learning journey and achievements.

**Attributes:**
- `user_id`: User identifier
- `topics_covered`: List of covered topics
- `questions_answered`: Total questions count
- `skills_acquired`: List of acquired skills
- `milestones`: Dictionary of milestone achievements
- `last_updated`: Last update timestamp

**Methods:**
- `validate()`: Validates progress data
- `add_topic()`: Adds a new topic
- `add_skill()`: Adds a new skill
- `increment_questions()`: Increments question counter
- `add_milestone()`: Records milestone achievement
- `to_dynamodb_item()`: Converts to DynamoDB format
- `from_dynamodb_item()`: Creates instance from DynamoDB data

### KnowledgeGap
Represents identified knowledge gaps for personalized learning.

**Attributes:**
- `gap_id`: Unique gap identifier
- `user_id`: User identifier
- `topic`: Topic where gap exists
- `detected_at`: Detection timestamp
- `confidence_score`: Detection confidence (0.0-1.0)
- `related_queries`: List of related query IDs
- `suggestions`: Learning suggestions
- `resolved`: Resolution status
- `resolved_at`: Resolution timestamp

**Methods:**
- `validate()`: Validates gap data
- `mark_resolved()`: Marks gap as resolved
- `add_suggestion()`: Adds learning suggestion
- `add_related_query()`: Adds related query ID
- `to_dynamodb_item()`: Converts to DynamoDB format
- `from_dynamodb_item()`: Creates instance from DynamoDB data

## Validation

All models include a `validate()` method that returns a tuple of `(is_valid: bool, error_message: Optional[str])`. This ensures data integrity before storage.

## DynamoDB Integration

All models provide:
- `to_dynamodb_item()`: Serializes to DynamoDB-compatible dictionary
- `from_dynamodb_item()`: Deserializes from DynamoDB item

Timestamps are stored as ISO 8601 strings for compatibility.

## Testing

Run tests with:
```bash
python -m pytest lambda/models/test_models.py -v
```

All models have comprehensive unit tests covering:
- Valid data scenarios
- Invalid data validation
- Edge cases
- DynamoDB conversion
- Helper methods
