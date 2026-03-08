"""
Document Indexing handler – S3 event triggered

Processes newly uploaded documents in the knowledge-base S3 bucket
through the ingestion pipeline (extract → chunk → embed → index).
"""

import json
import logging

from utils.config import Settings
from services.s3_ingestion_service import S3IngestionService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_settings = None
_ingestion = None


def _init():
    global _settings, _ingestion
    if _settings is None:
        _settings = Settings.from_env()
        _ingestion = S3IngestionService(_settings)


def lambda_handler(event, context):
    """
    Handle S3 object-created events for document indexing.

    The event contains one or more S3 records. Each record triggers
    the ingestion pipeline for the uploaded document.
    """
    _init()

    results = []
    records = event.get("Records", [])

    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Skip non-document files
        if key.endswith(".keep") or key.endswith("/"):
            logger.info("Skipping non-document key: %s", key)
            continue

        logger.info("Processing document: s3://%s/%s", bucket, key)

        try:
            result = _ingestion.process_document(bucket, key)
            results.append({
                "status": "success",
                "source_key": key,
                "document_id": result["document_id"],
                "chunks_indexed": result["chunks_indexed"],
            })
            logger.info(
                "Indexed %d chunks for %s",
                result["chunks_indexed"],
                key,
            )
        except Exception as exc:
            logger.exception("Failed to process %s", key)
            results.append({
                "status": "error",
                "source_key": key,
                "error": str(exc),
            })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "documents_processed": len(results),
            "results": results,
        }),
    }
