import http.client
from dataclasses import dataclass
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import Span, Tracer as Tracer, TracerProvider as TracerProvider
from typing import Any, Callable

METHOD_INDEX: int
URL_INDEX: int
BODY_INDEX: int
HEADERS_INDEX: int

@dataclass
class RequestInfo:
    """Container for HTTP request information passed to request hooks."""
    method: str
    url: str
    headers: dict[str, str]
    body: Any
    connection: http.client.HTTPConnection

@dataclass
class ResponseInfo:
    """Container for HTTP response information passed to response hooks."""
    status_code: int
    headers: dict[str, str]
    response: http.client.HTTPResponse
    connection: http.client.HTTPConnection
RequestHookT = Callable[[Span, RequestInfo], None]
ResponseHookT = Callable[[Span, ResponseInfo], None]

@dataclass
class InstrumentationContext:
    """Context for instrumentation configuration."""
    tracer: Tracer
    request_hook: RequestHookT | None
    response_hook: ResponseHookT | None

class HTTPClientInstrumentor(BaseInstrumentor):
    """Instrumentor for Python's http.client library.

    Wraps http.client.HTTPConnection.request() and getresponse() methods
    to create spans for HTTP requests.
    """
    def instrumentation_dependencies(self) -> list[str]:
        """Return list of instrumentation dependencies.

        Returns:
            list[str]: Empty list (http.client is stdlib).
        """
    def instrument(self, *, tracer_provider: TracerProvider | None = None, request_hook: RequestHookT | None = None, response_hook: ResponseHookT | None = None, **kwargs: Any) -> None:
        """Instrument the library.

        Args:
            tracer_provider: OpenTelemetry TracerProvider instance
            request_hook: Optional callback for request customization
            response_hook: Optional callback for response customization
            **kwargs: Additional keyword arguments
        """
