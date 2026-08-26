"""Gemini LLM provider implementation."""

import google.generativeai as genai

from app.ai.interfaces.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._model_name = model

    async def generate(self, prompt: str) -> str:
        response = await self._model.generate_content_async(prompt)
        return response.text

    async def generate_with_history(
        self,
        messages: list[dict],
        system_prompt: str = "",
    ) -> str:
        chat = self._model.start_chat(history=[])

        gemini_history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        chat = self._model.start_chat(history=gemini_history)

        last_message = messages[-1]["content"]
        if system_prompt:
            last_message = f"{system_prompt}\n\n{last_message}"

        response = await chat.send_message_async(last_message)
        return response.text
