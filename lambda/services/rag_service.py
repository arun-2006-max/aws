"""
RAG (Retrieval Augmented Generation) pipeline service.

Orchestrates the flow: embed query → search OpenSearch → augment prompt
→ invoke Bedrock model → return grounded response.
"""

import logging
from typing import Any, Optional

from utils.config import Settings
from services.bedrock_service import BedrockService
from services.opensearch_service import OpenSearchService

logger = logging.getLogger(__name__)

# System prompt template for RAG-augmented responses
_RAG_SYSTEM_PROMPT = """You are AI Builder Copilot, an intelligent learning and development assistant.
Answer the user's question using ONLY the provided context documents when relevant.
If the context does not contain enough information, say so and provide your best general knowledge.

CONTEXT DOCUMENTS:
{context}

INSTRUCTIONS:
- Cite specific documents when using information from them.
- Be concise and accurate.
- If debugging code, provide step-by-step analysis.
- If explaining concepts, use analogies and examples.
"""


class RAGService:
    """Orchestrates the Retrieval Augmented Generation pipeline."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings.from_env()
        self._bedrock = BedrockService(self._settings)
        self._opensearch = OpenSearchService(self._settings)

    def retrieve_and_generate(
        self,
        query: str,
        system_prompt_override: Optional[str] = None,
        max_documents: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Full RAG pipeline: embed → retrieve → augment → generate.

        Args:
            query: User's question or prompt.
            system_prompt_override: Custom system prompt (replaces default).
            max_documents: Number of context docs to retrieve.

        Returns:
            Dict with 'response', 'model', 'sources', 'input_tokens',
            'output_tokens'.
        """
        k = max_documents or self._settings.max_context_documents

        # Step 1 – Generate query embedding
        logger.info("Generating query embedding")
        query_embedding = self._bedrock.generate_embeddings(query)

        # Step 2 – Retrieve relevant documents from OpenSearch
        logger.info("Searching OpenSearch for top-%d documents", k)
        documents = self._opensearch.search_similar(query_embedding, k=k)

        # Step 3 – Build augmented prompt
        system_prompt = system_prompt_override or self._build_system_prompt(
            documents
        )

        # Step 4 – Invoke Bedrock with intelligent model selection
        logger.info("Invoking Bedrock model")
        result = self._bedrock.select_and_invoke(
            prompt=query,
            system_prompt=system_prompt,
        )

        # Step 5 – Attach source metadata
        result["sources"] = [
            {
                "source_key": doc["source_key"],
                "score": doc["score"],
                "document_id": doc["document_id"],
            }
            for doc in documents
        ]

        return result

    def retrieve_context(
        self,
        query: str,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant context documents without generating a response.

        Args:
            query: Search query.
            k: Number of results.

        Returns:
            List of document dicts from OpenSearch.
        """
        embedding = self._bedrock.generate_embeddings(query)
        return self._opensearch.search_similar(embedding, k=k)

    # ------------------------------------------------------------------
    # Prompt Construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_system_prompt(documents: list[dict]) -> str:
        """Build system prompt with retrieved context."""
        if not documents:
            context_text = "No relevant documents found."
        else:
            chunks = []
            for i, doc in enumerate(documents, 1):
                source = doc.get("source_key", "unknown")
                chunks.append(
                    f"[Document {i} | Source: {source}]\n{doc['text']}"
                )
            context_text = "\n\n".join(chunks)

        return _RAG_SYSTEM_PROMPT.format(context=context_text)
