"""Groq LLM provider implementation."""

from groq import AsyncGroq

from app.ai.interfaces.llm_provider import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def generate(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    async def generate_with_history(
        self,
        messages: list[dict],
        system_prompt: str = "",
    ) -> str:
        groq_messages = []

        if system_prompt:
            groq_messages.append({"role": "system", "content": system_prompt})

        groq_messages.extend(messages)

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=groq_messages,
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content
