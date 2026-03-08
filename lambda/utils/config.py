"""
Centralized configuration module.
All settings are loaded from environment variables – no hardcoded values.
"""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """
    Application settings loaded from environment variables.

    Usage:
        settings = Settings.from_env()
        table_name = settings.users_table
    """

    # Environment
    env: str = "dev"
    aws_region: str = "us-east-1"
    bedrock_region: str = "us-east-1"

    # DynamoDB table names
    users_table: str = ""
    sessions_table: str = ""
    interaction_logs_table: str = ""
    learning_progress_table: str = ""
    knowledge_gaps_table: str = ""
    response_cache_table: str = ""

    # S3 bucket names
    knowledge_base_bucket: str = ""
    logs_bucket: str = ""

    # OpenSearch
    opensearch_endpoint: str = ""
    opensearch_index: str = "knowledge_vectors"

    # Bedrock model IDs
    sonnet_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    haiku_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    titan_embed_model_id: str = "amazon.titan-embed-text-v2:0"

    # RAG settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_context_documents: int = 5

    # Cache TTL (seconds)
    response_cache_ttl: int = 3600

    @classmethod
    def from_env(cls) -> "Settings":
        """Create Settings from environment variables."""
        return cls(
            env=os.environ.get("ENV", "dev"),
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
            bedrock_region=os.environ.get("BEDROCK_REGION", "us-east-1"),
            users_table=os.environ.get("USERS_TABLE", ""),
            sessions_table=os.environ.get("SESSIONS_TABLE", ""),
            interaction_logs_table=os.environ.get("INTERACTION_LOGS_TABLE", ""),
            learning_progress_table=os.environ.get("LEARNING_PROGRESS_TABLE", ""),
            knowledge_gaps_table=os.environ.get("KNOWLEDGE_GAPS_TABLE", ""),
            response_cache_table=os.environ.get("RESPONSE_CACHE_TABLE", ""),
            knowledge_base_bucket=os.environ.get("KNOWLEDGE_BASE_BUCKET", ""),
            logs_bucket=os.environ.get("LOGS_BUCKET", ""),
            opensearch_endpoint=os.environ.get("OPENSEARCH_ENDPOINT", ""),
            opensearch_index=os.environ.get("OPENSEARCH_INDEX", "knowledge_vectors"),
            sonnet_model_id=os.environ.get(
                "SONNET_MODEL_ID",
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
            haiku_model_id=os.environ.get(
                "HAIKU_MODEL_ID",
                "anthropic.claude-3-haiku-20240307-v1:0",
            ),
            titan_embed_model_id=os.environ.get(
                "TITAN_EMBED_MODEL_ID",
                "amazon.titan-embed-text-v2:0",
            ),
            chunk_size=int(os.environ.get("CHUNK_SIZE", "512")),
            chunk_overlap=int(os.environ.get("CHUNK_OVERLAP", "50")),
            max_context_documents=int(
                os.environ.get("MAX_CONTEXT_DOCUMENTS", "5")
            ),
            response_cache_ttl=int(
                os.environ.get("RESPONSE_CACHE_TTL", "3600")
            ),
        )
