"""LLM Provider abstract interface."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        ...

    @abstractmethod
    async def generate_with_history(
        self,
        messages: list[dict],
        system_prompt: str = "",
    ) -> str:
        ...
