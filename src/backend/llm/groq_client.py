# src/backend/llm/groq_client.py

from __future__ import annotations

from typing import Optional

from groq import Groq

from .base_client import BaseLLMClient


class GroqClient(BaseLLMClient):
    """
    Concrete LLM client for Groq API.

    This is currently the ONLY fully-implemented provider.
    Other providers (e.g., OpenAI) can follow the same pattern.

    TODO[llm]:
      - Add optional streaming support if needed.
      - Expose more generation parameters (max_tokens, etc.).
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        super().__init__(model_name=model_name)
        self._client = Groq(api_key=api_key)

    def generate(self, prompt: str, *, temperature: Optional[float] = None) -> str:
        """
        Call Groq chat completions API and return raw text content.
        """
        if temperature is None:
            temperature = 0.1

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=temperature,
        )

        return response.choices[0].message.content
