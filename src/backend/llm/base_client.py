# src/backend/llm/base_client.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """
    Unified interface for all LLM providers.

    Concrete implementations:
      - OpenAIClient (src/backend/llm/openai_client.py)
      - GroqClient   (src/backend/llm/groq_client.py)

    The pipeline (LangGraph nodes) should depend only on this interface.
    """

    model_name: str

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @abstractmethod
    def generate(self, prompt: str, *, temperature: Optional[float] = None) -> str:
        """
        Synchronously call the underlying LLM and return plain text output.

        JSON parsing / Pydantic validation is handled in the pipeline layer.

        TODO:
          - Concrete implementations must:
            - Call provider API
            - Return the *raw* LLM text (no JSON parsing here)
        """
        raise NotImplementedError
