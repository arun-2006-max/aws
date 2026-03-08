"""
S3 document ingestion service for the RAG pipeline.

Downloads documents from S3, extracts text, chunks the content,
generates embeddings, and indexes them in OpenSearch.
"""

import io
import logging
import uuid
from typing import Optional

import boto3

from utils.config import Settings
from services.bedrock_service import BedrockService
from services.opensearch_service import OpenSearchService

logger = logging.getLogger(__name__)

# Supported document extensions
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


class S3IngestionService:
    """Processes documents from S3 into the OpenSearch vector index."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings.from_env()
        self._s3 = boto3.client(
            "s3", region_name=self._settings.aws_region
        )
        self._bedrock = BedrockService(self._settings)
        self._opensearch = OpenSearchService(self._settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_document(
        self,
        bucket: str,
        key: str,
    ) -> dict:
        """
        Full ingestion pipeline for a single S3 document.

        Steps:
            1. Download from S3
            2. Extract text
            3. Chunk into segments
            4. Generate embeddings per chunk
            5. Index into OpenSearch

        Args:
            bucket: S3 bucket name.
            key: S3 object key.

        Returns:
            Dict with 'document_id', 'chunks_indexed', 'source_key'.
        """
        document_id = str(uuid.uuid4())

        # 1 — Download
        logger.info("Downloading s3://%s/%s", bucket, key)
        raw_bytes = self.download_document(bucket, key)

        # 2 — Extract text
        extension = self._get_extension(key)
        text = self.extract_text(raw_bytes, extension)
        if not text.strip():
            logger.warning("No text extracted from %s", key)
            return {
                "document_id": document_id,
                "chunks_indexed": 0,
                "source_key": key,
            }

        # 3 — Chunk
        chunks = self.chunk_text(
            text,
            chunk_size=self._settings.chunk_size,
            overlap=self._settings.chunk_overlap,
        )
        logger.info("Split into %d chunks", len(chunks))

        # 4 + 5 — Embed & index
        for idx, chunk in enumerate(chunks):
            embedding = self._bedrock.generate_embeddings(chunk)
            self._opensearch.index_document(
                doc_id=document_id,
                text=chunk,
                embedding=embedding,
                source_key=key,
                chunk_index=idx,
                metadata={"bucket": bucket},
            )

        logger.info(
            "Indexed document %s (%d chunks)", document_id, len(chunks)
        )
        return {
            "document_id": document_id,
            "chunks_indexed": len(chunks),
            "source_key": key,
        }

    # ------------------------------------------------------------------
    # Sub-steps (exposed for testability)
    # ------------------------------------------------------------------

    def download_document(self, bucket: str, key: str) -> bytes:
        """Download a document from S3 and return raw bytes."""
        response = self._s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    @staticmethod
    def extract_text(raw_bytes: bytes, extension: str) -> str:
        """
        Extract plain text from document bytes.

        Args:
            raw_bytes: File content.
            extension: File extension (e.g. '.pdf').

        Returns:
            Extracted text string.
        """
        if extension in (".txt", ".md"):
            return raw_bytes.decode("utf-8", errors="replace")

        if extension == ".pdf":
            return S3IngestionService._extract_pdf(raw_bytes)

        if extension == ".docx":
            return S3IngestionService._extract_docx(raw_bytes)

        logger.warning("Unsupported extension: %s", extension)
        return ""

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> list[str]:
        """
        Split text into overlapping chunks by word count.

        Args:
            text: Full document text.
            chunk_size: Target words per chunk.
            overlap: Overlap words between consecutive chunks.

        Returns:
            List of text chunks.
        """
        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _get_extension(key: str) -> str:
        """Return the lowercase file extension including the dot."""
        dot_idx = key.rfind(".")
        if dot_idx == -1:
            return ""
        return key[dot_idx:].lower()

    @staticmethod
    def _extract_pdf(raw_bytes: bytes) -> str:
        """Extract text from PDF bytes using PyPDF2."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = [
                page.extract_text() or "" for page in reader.pages
            ]
            return "\n".join(pages)
        except ImportError:
            logger.error("PyPDF2 not installed; PDF extraction unavailable")
            return ""
        except Exception as exc:
            logger.error("PDF extraction failed: %s", exc)
            return ""

    @staticmethod
    def _extract_docx(raw_bytes: bytes) -> str:
        """Extract text from DOCX bytes using python-docx."""
        try:
            from docx import Document

            doc = Document(io.BytesIO(raw_bytes))
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n".join(paragraphs)
        except ImportError:
            logger.error(
                "python-docx not installed; DOCX extraction unavailable"
            )
            return ""
        except Exception as exc:
            logger.error("DOCX extraction failed: %s", exc)
            return ""
