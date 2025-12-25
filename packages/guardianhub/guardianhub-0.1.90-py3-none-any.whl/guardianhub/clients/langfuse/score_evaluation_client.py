"""Langfuse evaluation client.

This module provides a client for running evaluations and scoring in Langfuse.
"""

from __future__ import annotations
from typing import Optional
from langfuse import Langfuse
from guardianhub import get_logger
from .manager import LangfuseManager

LOGGER = get_logger(__name__)

class EvaluationClient:
    """Client for Langfuse evaluations."""

    def __init__(
        self,
        client: Optional[Langfuse] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs
    ):
        """Initialize the EvaluationClient.
        
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

    def score_trace(self, trace_id: str, name: str, value: float, comment: Optional[str] = None) -> None:
        """
        Scores a trace in Langfuse.

        Args:
            trace_id: The ID of the trace to score.
            name: The name of the score (e.g., "user-feedback").
            value: The score value.
            comment: An optional comment.
        """
        if not self._client:
            LOGGER.warning("Langfuse client not initialized. Cannot score trace.")
            return

        try:
            self._client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
            LOGGER.info("Successfully scored trace %s with score '%s'", trace_id, name)
        except Exception as e:
            LOGGER.error("Failed to score trace %s: %s", trace_id, e)

    def score_span(self, span_id: str, name: str, value: float, comment: Optional[str] = None) -> None:
        """
        Scores a span in Langfuse.

        Args:
            span_id: The ID of the span to score.
            name: The name of the score.
            value: The score value.
            comment: An optional comment.
        """
        if not self._client:
            LOGGER.warning("Langfuse client not initialized. Cannot score span.")
            return

        try:
            self._client.score(
                observation_id=span_id,
                name=name,
                value=value,
                comment=comment,
            )
            LOGGER.info("Successfully scored span %s with score '%s'", span_id, name)
        except Exception as e:
            LOGGER.error("Failed to score span %s: %s", span_id, e)
