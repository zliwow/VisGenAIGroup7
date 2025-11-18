# src/backend/llm/openai_client.py

from __future__ import annotations

from typing import Optional

from openai import OpenAI

from .base_client import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """
    Concrete LLM client for the OpenAI API.

    This class implements the BaseLLMClient interface so that the rest of the
    pipeline can switch between GroqClient and OpenAIClient seamlessly.

    Minimal version: synchronous call returning raw text.
    """

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        super().__init__(model_name=model_name)

        # NOTE:
        # The new OpenAI Python SDK uses `OpenAI(api_key=...)`
        # See: https://platform.openai.com/docs/api-reference/introduction
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, *, temperature: Optional[float] = None) -> str:
        """
        Call OpenAI's chat completion API and return the text content.

        TODO[llm]:
          - Add support for structured JSON mode (response_format={"type": "json_object"})
          - Add control for max_tokens, top_p, etc.
          - Add streaming if needed.
        """
        if temperature is None:
            temperature = 0.1

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048,
        )

        # New OpenAI SDK returns:
        # response.choices[0].message.content
        return response.choices[0].message.content
