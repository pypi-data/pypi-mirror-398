from _typeshed import Incomplete
from bosa_core.telemetry.opentelemetry.initializer import OpenTelemetryConfig as OpenTelemetryConfig, init_otel_sentry as init_otel_sentry
from typing import Any

class SentryConfig:
    """Configuration object for Sentry initialization.

    this class is used to store the configuration for Sentry initialization.
    """
    dsn: Incomplete
    environment: Incomplete
    release: Incomplete
    profiles_sample_rate: Incomplete
    send_default_pii: Incomplete
    traces_sampler: Incomplete
    open_telemetry_config: Incomplete
    additional_options: Incomplete
    def __init__(self, dsn: str | None = None, environment: str | None = None, release: str | None = None, profiles_sample_rate: float | None = None, send_default_pii: bool | None = None, traces_sampler=None, open_telemetry_config: OpenTelemetryConfig | None = None, **kwargs: Any) -> None:
        """Initializes the Sentry configuration object with the specified parameters.

        Args:
            dsn (str): The Data Source Name (DSN) for the Sentry project.
            environment (str): The environment for the Sentry project.
            release (str): The release version for the Sentry project.
            profiles_sample_rate (float): The sample rate for performance monitoring.
            send_default_pii (bool): Whether to send default Personally Identifiable Information (PII).
            traces_sampler (TracesSampler): The sampler for traces.
            open_telemetry_config: The OpenTelemetry Config
            **kwargs: Additional keyword arguments to pass to sentry_sdk.init
        """

def init_sentry(config: SentryConfig | None = None) -> None:
    """Initializes Sentry for error tracking and performance monitoring.

    Initializes Sentry with the specified parameters.

    Args:
        config (SentryConfig | None, optional): The configuration object for Sentry initialization. Defaults to None.
    """
