# llm/llm_service.py
import json
from typing import Dict, Any, Optional, Type, TypeVar, List, Union

import httpx
from pydantic import BaseModel, ValidationError

from guardianhub import get_logger

logger = get_logger(__name__)
from guardianhub.config import settings

T = TypeVar('T', bound=BaseModel)

class LLMClient:
    """Unified client for LLM interactions with structured output support."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=240.0
        )

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model_key: str = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            response_format: Optional[Dict[str, str]] = None,
            response_model: Optional[Type[T]] = None,
            **kwargs
    ) -> Union[Dict[str, Any], T]:
        """
        Send a chat completion request to the LLM service.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model_key: The model key to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            response_format: Optional format specification for the response
            response_model: Optional Pydantic model for structured output
            **kwargs: Additional arguments to pass to the API

        Returns:
            Dict containing the API response or an instance of response_model if provided

        Raises:
            RuntimeError: If the API request fails
            ValidationError: If response_model is provided and the response doesn't match the schema
        """
        # Set defaults from settings if not provided
        model_key = model_key or getattr(settings.llm, 'model_key', 'default')
        temperature = temperature if temperature is not None else getattr(settings.llm, 'temperature', 0.7)
        max_tokens = max_tokens if max_tokens is not None else getattr(settings.llm, 'max_tokens', 1000)

        # Prepare the base payload
        payload = {
            "model": getattr(settings.llm, 'model_name', 'gpt-3.5-turbo'),
            "model_key": model_key,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **{k: v for k, v in kwargs.items() if v is not None}
        }

        # For structured output, include the schema in the request
        if response_model is not None:
            payload["response_schema"] = response_model.model_json_schema()
            payload["response_model"] = response_model.__name__

        try:
            response = await self.client.post(
                "/v1/chat/completions",
                json=payload,
                timeout=360.0
            )
            response.raise_for_status()
            response_data = response.json()

            logger.debug(f"Received Response Data: {response_data}")

            if "choices" in response_data:
                content = response_data["choices"][0]["message"].get("content")

                if content and isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass

                if response_model and content:
                    try:
                        return response_model.parse_obj(content)
                    except ValidationError as e:
                        logger.error(f"Response validation failed: {e}")
                        logger.debug(f"Response content: {content}")
                        raise

                return content or response_data

            return response_data

        except httpx.HTTPStatusError as e:
            error_msg = "LLM API error ({}): {}".format(e.response.status_code, e.response.text)
            logger.error(error_msg)
            raise RuntimeError("LLM service error: {}".format(error_msg)) from e
        except Exception as e:
            logger.error("Unexpected error: {}".format(str(e)), exc_info=True)
            raise RuntimeError("LLM client error: {}".format(str(e))) from e

    async def generate_structured(
            self,
            messages: List[Dict[str, str]],
            response_model: Type[T],
            **kwargs
    ) -> T:
        """
        Generate a structured response using the specified model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            response_model: Pydantic model class for the expected output structure
            **kwargs: Additional arguments to pass to chat_completion

        Returns:
            An instance of the provided response_model with the generated content

        Raises:
            RuntimeError: If the API request fails
            ValidationError: If the response doesn't match the schema
        """
        return await self.chat_completion(
            messages=messages,
            response_model=response_model,
            **kwargs
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()