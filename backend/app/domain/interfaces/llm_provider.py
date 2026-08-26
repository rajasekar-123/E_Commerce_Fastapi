"""
LLM Provider abstract interface.

Follows Open/Closed + Liskov Substitution principles:
  - Open for extension (add new providers without modifying AIService)
  - Any provider can substitute another without breaking business logic
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract LLM provider interface.

    Implementations:
      - GeminiProvider (google-generativeai)
      - GroqProvider (groq SDK)
      - OllamaProvider (local Ollama HTTP API)
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a text response for the given prompt.

        Args:
            prompt: The full prompt string including context and instruction.

        Returns:
            Generated text response.
        """
        ...

    @abstractmethod
    async def generate_with_history(
        self,
        messages: list[dict],
        system_prompt: str = "",
    ) -> str:
        """
        Generate a response given a conversation history.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            system_prompt: Optional system instruction.

        Returns:
            Generated text response.
        """
        ...
