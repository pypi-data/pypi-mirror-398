"""Main Langfuse client for Guardian Hub SDK.

This module provides a centralized client that acts as a facade for various
Langfuse functionalities, including tracing, prompt management, and evaluations.
"""

from __future__ import annotations

import os
from typing import Optional

from .langfuse.score_evaluation_client import EvaluationClient
from .langfuse.manager import LangfuseManager
from .langfuse.prompt_client import PromptClient
from .langfuse.tracing_client import TracingClient

from guardianhub import get_logger

LOGGER = get_logger(__name__)


class LangfuseClient:
    """A facade client for Langfuse, providing access to tracing, prompts, and evaluations.
    
    This client centralizes access to Langfuse functionalities by using a manager
    to handle the singleton connection.

    Args:
        public_key: Langfuse public key (optional, can be set via LANGFUSE_PUBLIC_KEY env var).
        secret_key: Langfuse secret key (optional, can be set via LANGFUSE_SECRET_KEY env var).
        host: Langfuse host URL (optional, can be set via LANGFUSE_HOST env var).
        **kwargs: Additional arguments to pass to the Langfuse client constructor.
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs
    ):
        """Initialize the main Langfuse client and its sub-clients."""
        # Get the singleton Langfuse instance from the manager
        self._client = LangfuseManager.get_instance(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            **kwargs
        )
        
        # Initialize specialized clients, passing the core client instance
        self.tracing = TracingClient(self._client)
        self.prompts = PromptClient(self._client)
        self.evaluations = EvaluationClient(self._client)

    @property
    def is_initialized(self) -> bool:
        """Check if the core Langfuse client is initialized."""
        return self._client is not None

    def flush(self) -> None:
        """Flush the Langfuse client to ensure all buffered data is sent."""
        LangfuseManager.flush()