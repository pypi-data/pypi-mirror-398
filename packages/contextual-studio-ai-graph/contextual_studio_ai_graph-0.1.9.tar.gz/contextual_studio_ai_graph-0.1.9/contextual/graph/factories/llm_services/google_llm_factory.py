import os
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from ...exceptions.factories.llm_services.llm_service_exceptions import (
    LLMServiceConnectionException,
)


class GoogleLLMFactory:
    """Concrete factory for creating Google Generative AI LLM services using ChatGoogleGenerativeAI."""

    @staticmethod
    def create(**kwargs: Any) -> ChatGoogleGenerativeAI:
        """Creates an instance of ChatGoogleGenerativeAI."""
        # 1. API Key validation: prioritize kwargs, then environment
        api_key = (
            kwargs.get("api_key")
            or kwargs.get("google_api_key")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if not api_key:
            raise LLMServiceConnectionException(
                "GOOGLE_API_KEY not found in environment or arguments."
            )

        # 2. Set defaults if not provided
        kwargs.setdefault("model", os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-flash"))
        kwargs.setdefault("temperature", 0)
        kwargs.setdefault("max_retries", 2)
        kwargs.setdefault("max_tokens", None)
        kwargs.setdefault("timeout", None)

        # 3. Ensure LangChain gets its expected key name
        if "google_api_key" not in kwargs:
            kwargs["google_api_key"] = api_key
            kwargs.pop("api_key", None)  # Clean up generic key name

        return ChatGoogleGenerativeAI(**kwargs)
