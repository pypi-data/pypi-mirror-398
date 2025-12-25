"""Langfuse prompt management client.

This module provides a client for managing prompts in Langfuse.
"""

from __future__ import annotations

from typing import Optional, Union

from langfuse import Langfuse

from guardianhub import get_logger
from .manager import LangfuseManager

LOGGER = get_logger(__name__)


class PromptClient:
    """Client for Langfuse prompt management."""

    def __init__(
        self,
        client: Optional[Langfuse] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs
    ):
        """Initialize the PromptClient.
        
        Args:
            client: Optional Langfuse client instance. If not provided, will use LangfuseManager.
            public_key: Langfuse public key. If not provided, will use LANGFUSE_PUBLIC_KEY from environment.
            secret_key: Langfuse secret key. If not provided, will use LANGFUSE_SECRET_KEY from environment.
            host: Langfuse host URL. If not provided, will use LANGFUSE_HOST from environment or default.
            **kwargs: Additional arguments to pass to Langfuse client initialization.
        """
        if client is not None:
            self._client = client
        else:
            self._client = LangfuseManager.get_instance(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
                **kwargs
            )

    def get_prompt(self, name: str, version: Optional[int] = None) -> Optional[str]:
        """
        Retrieves a prompt from Langfuse.

        Args:
            name: The name of the prompt.
            version: The version of the prompt (optional).

        Returns:
            The prompt string, or None if not found.
        """
        if not self._client:
            LOGGER.warning("Langfuse client not initialized. Cannot fetch prompt.")
            return None
        
        try:
            prompt = self._client.get_prompt(name, version)
            return prompt.prompt
        except Exception as e:
            LOGGER.error("Failed to retrieve prompt '%s': %s", name, e)
            return None
