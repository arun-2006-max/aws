"""
Amazon Bedrock integration service.

Provides model invocation for Claude Sonnet, Claude Haiku,
and Titan Embeddings. Supports intelligent model routing based
on query complexity.
"""

import json
import logging
from typing import Any, Optional

import boto3

from utils.config import Settings

logger = logging.getLogger(__name__)


class BedrockService:
    """Client wrapper for Amazon Bedrock model invocations."""

    # Complexity thresholds for model routing
    _COMPLEX_KEYWORDS = frozenset([
        "debug", "explain", "architecture", "design", "refactor",
        "optimize", "analyze", "compare", "implement", "migrate",
        "security", "performance", "scale", "deploy",
    ])

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings.from_env()
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=self._settings.bedrock_region,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def invoke_sonnet(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Invoke Claude 3.5 Sonnet for complex reasoning tasks.

        Args:
            prompt: User message.
            system_prompt: Optional system instruction.
            max_tokens: Maximum response tokens.
            temperature: Sampling temperature.

        Returns:
            Dict with 'response', 'model', 'input_tokens', 'output_tokens'.
        """
        return self._invoke_claude(
            model_id=self._settings.sonnet_model_id,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def invoke_haiku(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.5,
    ) -> dict[str, Any]:
        """
        Invoke Claude Haiku for cost-optimized lightweight tasks.

        Args:
            prompt: User message.
            system_prompt: Optional system instruction.
            max_tokens: Maximum response tokens.
            temperature: Sampling temperature.

        Returns:
            Dict with 'response', 'model', 'input_tokens', 'output_tokens'.
        """
        return self._invoke_claude(
            model_id=self._settings.haiku_model_id,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def generate_embeddings(self, text: str) -> list[float]:
        """
        Generate vector embeddings using Amazon Titan Embeddings v2.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        body = json.dumps({
            "inputText": text,
            "dimensions": 1024,
            "normalize": True,
        })

        response = self._client.invoke_model(
            modelId=self._settings.titan_embed_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        result = json.loads(response["body"].read())
        return result["embedding"]

    def select_and_invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Intelligently select the best model and invoke it.

        Uses Sonnet for complex queries, Haiku for simple ones.

        Args:
            prompt: User message.
            system_prompt: Optional system instruction.

        Returns:
            Dict with 'response', 'model', 'input_tokens', 'output_tokens'.
        """
        if self._is_complex_query(prompt):
            logger.info("Routing to Sonnet (complex query)")
            return self.invoke_sonnet(prompt, system_prompt)
        logger.info("Routing to Haiku (simple query)")
        return self.invoke_haiku(prompt, system_prompt)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _invoke_claude(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Invoke a Claude model via the Messages API."""
        messages = [{"role": "user", "content": prompt}]

        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            body["system"] = system_prompt

        response = self._client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        result = json.loads(response["body"].read())
        response_text = result["content"][0]["text"]

        return {
            "response": response_text,
            "model": model_id,
            "input_tokens": result.get("usage", {}).get("input_tokens", 0),
            "output_tokens": result.get("usage", {}).get("output_tokens", 0),
        }

    def _is_complex_query(self, prompt: str) -> bool:
        """Heuristic: check if the query warrants Sonnet."""
        lower = prompt.lower()
        # Long queries or those containing complexity keywords → Sonnet
        if len(prompt) > 500:
            return True
        return any(kw in lower for kw in self._COMPLEX_KEYWORDS)
