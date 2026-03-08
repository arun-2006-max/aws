"""OpenRouter AI service — OpenAI-compatible API."""
import os
import httpx
from typing import Optional


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-builder-copilot.vercel.app",
            "X-Title": "AI Builder Copilot",
        }

    async def chat(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "openai/gpt-4o-mini",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Send a chat completion request to OpenRouter."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return {
            "response": content,
            "model": model,
            "usage": data.get("usage", {}),
        }

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using OpenRouter (text-embedding-3-small via OpenAI)."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BASE_URL}/embeddings",
                headers=self.headers,
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": text[:8000],  # Truncate to token limit
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return data["data"][0]["embedding"]
