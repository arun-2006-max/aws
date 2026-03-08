"""
Amazon OpenSearch Service integration for vector search.

Manages the knowledge_vectors index and provides kNN similarity search
for the RAG pipeline.
"""

import json
import logging
from typing import Any, Optional

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from utils.config import Settings

logger = logging.getLogger(__name__)

# Titan Embeddings v2 produces 1024-dimensional vectors
EMBEDDING_DIMENSION = 1024


class OpenSearchService:
    """Client for OpenSearch vector operations."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings.from_env()
        self._index_name = self._settings.opensearch_index
        self._client = self._build_client()

    # ------------------------------------------------------------------
    # Index Management
    # ------------------------------------------------------------------

    def create_index(self) -> dict:
        """
        Create the knowledge_vectors index with kNN vector mapping.

        Returns:
            OpenSearch create-index response.
        """
        if self._client.indices.exists(index=self._index_name):
            logger.info("Index '%s' already exists", self._index_name)
            return {"acknowledged": True, "already_exists": True}

        body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512,
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": EMBEDDING_DIMENSION,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16,
                            },
                        },
                    },
                    "text": {"type": "text"},
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "source_key": {"type": "keyword"},
                    "metadata": {"type": "object", "enabled": False},
                }
            },
        }

        response = self._client.indices.create(
            index=self._index_name, body=body
        )
        logger.info("Created index '%s'", self._index_name)
        return response

    # ------------------------------------------------------------------
    # Document Operations
    # ------------------------------------------------------------------

    def index_document(
        self,
        doc_id: str,
        text: str,
        embedding: list[float],
        source_key: str,
        chunk_index: int = 0,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Index a document chunk with its embedding vector.

        Args:
            doc_id: Unique document identifier.
            text: Chunk text content.
            embedding: Vector embedding of the text.
            source_key: S3 object key of the source document.
            chunk_index: Position of this chunk in the source document.
            metadata: Optional metadata dict.

        Returns:
            OpenSearch index response.
        """
        body = {
            "embedding": embedding,
            "text": text,
            "document_id": doc_id,
            "chunk_index": chunk_index,
            "source_key": source_key,
            "metadata": metadata or {},
        }

        response = self._client.index(
            index=self._index_name,
            id=f"{doc_id}_{chunk_index}",
            body=body,
            refresh="wait_for",
        )
        return response

    def search_similar(
        self,
        embedding: list[float],
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Perform kNN similarity search.

        Args:
            embedding: Query embedding vector.
            k: Number of nearest neighbours to return.

        Returns:
            List of dicts with 'text', 'score', 'source_key', 'metadata'.
        """
        body = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": k,
                    }
                }
            },
            "_source": ["text", "document_id", "source_key", "metadata"],
        }

        response = self._client.search(
            index=self._index_name, body=body
        )

        results = []
        for hit in response.get("hits", {}).get("hits", []):
            results.append({
                "text": hit["_source"]["text"],
                "score": hit["_score"],
                "source_key": hit["_source"].get("source_key", ""),
                "document_id": hit["_source"].get("document_id", ""),
                "metadata": hit["_source"].get("metadata", {}),
            })

        logger.info("Found %d similar documents", len(results))
        return results

    def delete_document(self, document_id: str) -> dict:
        """
        Delete all chunks for a given document.

        Args:
            document_id: Document identifier to delete.

        Returns:
            OpenSearch delete-by-query response.
        """
        body = {
            "query": {
                "term": {"document_id": document_id}
            }
        }
        return self._client.delete_by_query(
            index=self._index_name, body=body
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_client(self) -> OpenSearch:
        """Build an authenticated OpenSearch client."""
        endpoint = self._settings.opensearch_endpoint
        if not endpoint:
            logger.warning("OPENSEARCH_ENDPOINT not set; using localhost")
            endpoint = "localhost"

        region = self._settings.aws_region
        credentials = boto3.Session().get_credentials()
        aws_auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "es",
            session_token=credentials.token,
        )

        return OpenSearch(
            hosts=[{"host": endpoint, "port": 443}],
            http_auth=aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )
