"""
Ollama LLM provider implementation.
Uses httpx to call local Ollama HTTP API — no vendor SDK required.
"""

import httpx

from app.domain.interfaces.llm_provider import LLMProvider


class OllamaProvider(LLMProvider):
    """
    Ollama local LLM provider.
    Implements LLMProvider interface — substitutable with Gemini or Groq.

    Requires a running Ollama instance (e.g. ollama serve).
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, prompt: str) -> str:
        """Generate a single-turn response via Ollama /api/generate."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]

    async def generate_with_history(
        self,
        messages: list[dict],
        system_prompt: str = "",
    ) -> str:
        """Generate a response using Ollama /api/chat with conversation history."""
        ollama_messages = []

        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})

        ollama_messages.extend(messages)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={"model": self._model, "messages": ollama_messages, "stream": False},
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
