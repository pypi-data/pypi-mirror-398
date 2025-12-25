from typing import Optional

from fastapi import Request
from opentelemetry import baggage
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.propagate import extract
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span


async def bind_otel_context(request: Request, call_next):
    # 1️⃣ Extract OTEL context from headers
    ctx = extract(request.headers)

    # 2️⃣ Attach context so downstream sees it
    with trace.use_span(trace.get_current_span(ctx), end_on_exit=False):
        return await call_next(request)

class BaggageToSpanProcessor(SpanProcessor):
    """
    Copies selected baggage values into span attributes
    so they appear on every span.
    """

    BAGGAGE_KEYS = (
        "user_id",
        "session_id",
    )

    def on_start( self,
        span: Span,
        parent_context: Optional[Context] = None,
    ) -> None:
        for key in self.BAGGAGE_KEYS:
            value = baggage.get_baggage(key, parent_context)
            if value is not None:
                span.set_attribute(key, str(value))

    def on_end(self, span):
        pass