"""Langfuse tracing client for observability.

This module provides a client for tracing and logging.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Dict, Optional

from langfuse import Langfuse, LangfuseSpan
from langfuse.api.client import TraceClient as Trace

from guardianhub import get_logger
from .manager import LangfuseManager

LOGGER = get_logger(__name__)


class TracingClient:
    """Client for Langfuse tracing, spans, and events."""
    _current_trace: ContextVar[Optional[Trace]] = ContextVar("_current_trace", default=None)
    _current_span: ContextVar[Optional[LangfuseSpan]] = ContextVar("_current_span", default=None)

    def __init__(
        self,
        client: Optional[Langfuse] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs
    ):
        """Initialize the TracingClient.
        
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
        self.default_trace_tags: Dict[str, Any] = {}
        self.default_span_tags: Dict[str, Any] = {}

    @property
    def is_initialized(self) -> bool:
        return self._client is not None

    def set_default_trace_tags(self, tags: Dict[str, Any]) -> None:
        self.default_trace_tags.update(tags)

    def set_default_span_tags(self, tags: Dict[str, Any]) -> None:
        self.default_span_tags.update(tags)

    def get_current_trace(self) -> Optional[Trace]:
        return self._current_trace.get()

    def get_current_span(self) -> Optional[LangfuseSpan]:
        """Get the current active span.
        
        Returns:
            Optional[LangfuseSpan]: The current active span, or None if no span is active.
        """
        return self._current_span.get()

    def start_trace(
        self,
        name: str,
        tags: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Trace]:
        if not self.is_initialized:
            LOGGER.debug("Langfuse client not initialized. Skipping trace creation.")
            return None
        
        if not name or not isinstance(name, str):
            raise ValueError("Trace name must be a non-empty string")
            
        merged_tags = {**self.default_trace_tags, **(tags or {})}
        
        try:
            trace = self._create_trace(
                name=name, 
                tags=merged_tags, 
                metadata=metadata or {},
                **kwargs
            )
            self._current_trace.set(trace)
            LOGGER.debug("Started trace: %s", name)
            return trace
        except Exception as e:
            LOGGER.error("Failed to start trace '%s': %s", name, str(e), exc_info=True)
            return None

    def end_trace(self, trace: Optional[Trace] = None) -> None:
        trace_to_end = trace or self.get_current_trace()
        if not trace_to_end:
            LOGGER.debug("No active trace to end")
            return
            
        try:
            self._end_trace(trace_to_end)
            LOGGER.debug("Ended trace: %s", getattr(trace_to_end, 'id', 'unknown'))
        except Exception as e:
            LOGGER.exception("Error ending trace: %s", str(e))
        finally:
            if self.get_current_trace() is trace_to_end:
                self._current_trace.set(None)
                self._current_span.set(None)

    def start_span(
        self, 
        name: str, 
        tags: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LangfuseSpan]:
        if not self.is_initialized:
            LOGGER.debug("Langfuse client not initialized. Skipping span creation.")
            return None

        if not name or not isinstance(name, str):
            raise ValueError("Span name must be a non-empty string")
            
        trace = self.get_current_trace()
        
        if not trace:
            trace_name = f"auto-trace-{name}"
            LOGGER.debug("No active trace found. Creating new trace: %s", trace_name)
            trace = self.start_trace(name=trace_name, tags=tags, metadata=metadata)
            if not trace:
                LOGGER.error("Failed to auto-create trace for span '%s'", name)
                return None

        merged_tags = {**self.default_span_tags, **(tags or {})}

        try:
            span = self._create_span(trace, name, merged_tags, metadata or {}, **kwargs)
            self._current_span.set(span)
            LOGGER.debug("Started span '%s' in trace %s", name, getattr(trace, 'id', 'unknown'))
            return span
        except Exception as e:
            LOGGER.error("Failed to start span '%s': %s", name, str(e), exc_info=True)
            return None

    def end_span(self, span: Optional[LangfuseSpan] = None) -> None:
        span_to_end = span or self.get_current_span()
        if not span_to_end:
            LOGGER.debug("No active span to end")
            return
            
        try:
            self._end_span(span_to_end)
            LOGGER.debug("Ended span: %s", getattr(span_to_end, 'id', 'unknown'))
        except Exception as e:
            LOGGER.exception("Error ending span: %s", str(e))
        finally:
            if self.get_current_span() is span_to_end:
                self._current_span.set(None)

    def start_agent_trace(self, agent_name: str, agent_version: Optional[str] = None,
                          task_type: Optional[str] = None, domain: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[Trace]:
        tags = {"agent_name": agent_name}
        if agent_version:
            tags["agent_version"] = agent_version
        if task_type:
            tags["task_type"] = task_type
        if domain:
            tags["domain"] = domain

        return self.start_trace(name=f"agent:{agent_name}", tags=tags, metadata=metadata)

    def log_agent_step(self, step_type: str, input_data: Optional[Any] = None, output_data: Optional[Any] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Optional[LangfuseSpan]:
        metadata = metadata or {}
        metadata.update({"input": input_data, "output": output_data})
        return self.start_span(name=f"step:{step_type}", tags={"step_type": step_type}, metadata=metadata)

    def log_tool_call(self, tool_name: str, status: str = "success", error: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[LangfuseSpan]:
        metadata = metadata or {}
        if error:
            metadata["error_message"] = error
        span = self.start_span(name=f"tool:{tool_name}", tags={"tool_name": tool_name, "tool_status": status},
                               metadata=metadata)
        if span:
            self.end_span(span)
        return span

    def log_reflection_event(self, event_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        trace = self.get_current_trace()
        if not trace:
            LOGGER.warning("No active trace for reflection event %s", event_name)
            return
        try:
            trace.event(name=event_name, metadata=metadata or {})
        except Exception:
            LOGGER.exception("Failed to log reflection event")

    def _create_trace(
        self, 
        name: str, 
        tags: Dict[str, Any], 
        metadata: Dict[str, Any],
        **kwargs
    ) -> Trace:
        if not self._client:
            raise RuntimeError("Langfuse client is not initialized")
        
        tag_list = [f"{k}:{v}" for k, v in tags.items()]
        
        return self._client.trace(
            name=name,
            metadata=metadata,
            tags=tag_list,
            **kwargs
        )

    def _end_trace(self, trace: Trace) -> None:
        trace.end()

    def _create_span(
        self, 
        trace: Trace,
        name: str, 
        tags: Dict[str, Any], 
        metadata: Dict[str, Any],
        **kwargs
    ) -> LangfuseSpan:
        tag_list = [f"{k}:{v}" for k, v in tags.items()]
        return trace.span(
            name=name,
            metadata=metadata,
            tags=tag_list,
            **kwargs
        )

    def _end_span(self, span: LangfuseSpan) -> None:
        span.end()
