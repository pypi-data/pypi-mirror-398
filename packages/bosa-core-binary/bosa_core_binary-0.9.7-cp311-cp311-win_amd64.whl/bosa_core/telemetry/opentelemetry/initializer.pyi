from _typeshed import Incomplete
from fastapi import FastAPI as FastAPI
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import Sampler as Sampler

class FastAPIConfig:
    """Configuration class for FastAPI application."""
    app: Incomplete
    def __init__(self, app: FastAPI) -> None:
        """Initializes FastAPIConfig with a FastAPI application.

        Args:
            app (FastAPI): The FastAPI application to configure.
        """

class OpenTelemetryConfig:
    """Configuration-based initializer for OpenTelemetry with FastAPI and Langchain support."""
    provider: TracerProvider | None
    endpoint: Incomplete
    trace_sampler: Incomplete
    headers: Incomplete
    attributes: Incomplete
    use_grpc: Incomplete
    fastapi_config: Incomplete
    use_langchain: Incomplete
    use_httpx: Incomplete
    use_requests: Incomplete
    disable_sentry_distributed_tracing: Incomplete
    def __init__(self, endpoint: str = '', trace_sampler: Sampler = None, headers: dict[str, str] = None, attributes: dict[str, str] = None, use_grpc: bool = True, fastapi_config: FastAPIConfig | None = None, use_langchain: bool = False, use_httpx: bool = True, use_requests: bool = True, disable_sentry_distributed_tracing: bool = False) -> None:
        '''Initializes OpenTelemetryConfig with optional attributes.

        Args:
            endpoint (str): The OTLP endpoint. If you have port, please concat with the endpoint, e.g. "localhost:4317".
            trace_sampler (Sampler): The sampler for traces.
            headers (dict[str, str]): Headers with key value for connecting to the exporter.
            attributes (dict[str, str]): Additional resource attributes.
            use_grpc (bool): use grpc for opentelemetry exporter.
            fastapi_config (FastAPI | None): The FastAPI fastapi_config (if using FastAPI tracing).
            use_langchain (bool): Whether to use Langchain tracing.
            use_httpx (bool): Whether to use httpx for tracing.
            use_requests (bool): Whether to use requests for tracing.
            disable_sentry_distributed_tracing (bool): Disable Sentry distributed tracing.
        '''

def init_otel_with_external_exporter(initializer: OpenTelemetryConfig) -> None:
    """Initializes OpenTelemetry with an external exporter.

    This method initializes OpenTelemetry with an external exporter (OTLP)
        and instruments FastAPI and Langchain if applicable.

    Args:
        initializer (OpenTelemetryConfig): The configuration for OpenTelemetry.
    """
def init_otel_sentry(initializer: OpenTelemetryConfig) -> None:
    """Initializes OpenTelemetry tracing.

    This method initializes OpenTelemetry with Sentry and instruments FastAPI and Langchain if applicable.

    Args:
        initializer (OpenTelemetryConfig): The configuration for OpenTelemetry.
    """
