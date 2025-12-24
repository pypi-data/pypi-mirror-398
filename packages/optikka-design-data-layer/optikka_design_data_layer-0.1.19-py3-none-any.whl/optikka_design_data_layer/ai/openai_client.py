"""
OpenAI client
"""

from typing import Optional, Type, Any
from openai import OpenAI

from optikka_design_data_layer.utils.secrets_manager import SecretsManager
from optikka_design_data_layer.utils.config import EnvironmentVariables


class OpenAIClient:
    """
    OpenAI client wrapper
    """

    def __init__(
        self,
        secret_arn: Optional[str] = None,
        secrets_manager: Optional[SecretsManager] = None,
        default_model: str = "gpt-4o-2024-08-06",
    ) -> None:
        resolved_secret_arn = (
            secret_arn or EnvironmentVariables.OPENAI_API_KEY_SECRET_ARN
        )

        if not resolved_secret_arn:
            raise RuntimeError(
                "OPENAI_API_KEY_SECRET_ARN must be set in env or provided explicitly"
            )

        self._secret_arn = resolved_secret_arn
        self._secrets_manager = secrets_manager or SecretsManager()
        self._default_model = default_model
        self._client: OpenAI | None = None

    def get_client(self) -> OpenAI:
        """Return a cached OpenAI client, creating it if needed."""
        if self._client is not None:
            return self._client
        api_key = self._secrets_manager.get_openai_api_key(self._secret_arn)
        self._client = OpenAI(api_key=api_key)
        return self._client

    def invoke(
        self,
        model: Optional[str],
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Invoke a chat completion request.
        """
        client = self.get_client()
        chosen_model = model or self._default_model
        if not chosen_model:
            raise RuntimeError(
                "Model must be provided either in invoke() or as default_model in __init__"
            )
        params = {"model": chosen_model, "messages": messages}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(kwargs)
        return client.chat.completions.create(**params)

    def parse(
        self,
        input_messages: list[dict],
        response_format: Type[Any],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """Structured output parsing via Responses API; returns parsed model instance."""
        client = self.get_client()
        chosen_model = model or self._default_model
        if not chosen_model:
            raise RuntimeError(
                "Model must be provided either in parse() or as default_model in __init__"
            )
        params = {"model": chosen_model, "input": input_messages, "response_format": response_format}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_output_tokens"] = max_tokens
        params.update(kwargs)

        return client.beta.chat.completions.parse(**params)


# Lazy initialization to avoid instantiation on import
_openai_instance = None

class _OpenAIClientProxy:
    """
    Lazy-loading proxy for OpenAIClient singleton.

    The actual OpenAIClient instance is only created when first accessed,
    not when the module is imported. This prevents initialization errors in
    Lambda functions that don't use OpenAI.
    """
    def __getattr__(self, name):
        global _openai_instance
        if _openai_instance is None:
            _openai_instance = OpenAIClient()
        return getattr(_openai_instance, name)

openai_client = _OpenAIClientProxy()
