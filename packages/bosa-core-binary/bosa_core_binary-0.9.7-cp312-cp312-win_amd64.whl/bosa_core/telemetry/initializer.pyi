from _typeshed import Incomplete
from bosa_core.telemetry.opentelemetry.initializer import OpenTelemetryConfig as OpenTelemetryConfig, init_otel_with_external_exporter as init_otel_with_external_exporter
from bosa_core.telemetry.sentry.initializer import SentryConfig as SentryConfig, init_sentry as init_sentry

class TelemetryConfig:
    """Configuration class for telemetry config."""
    sentry_config: Incomplete
    otel_config: Incomplete
    def __init__(self, sentry_config: SentryConfig | None = None, otel_config: OpenTelemetryConfig | None = None) -> None:
        """Initializes the telemetry configuration object with the specified parameters.

        Args:
            sentry_config (SentryConfig): The Sentry configuration.
            otel_config: The OpenTelemetry config.
        """

def init_telemetry(config: TelemetryConfig) -> None:
    """Initializes telemetry for error tracking and performance monitoring.

    Initializes telemetry with the specified parameters.

    Args:
        config (TelemetryConfig): The telemetry configuration.
    """
