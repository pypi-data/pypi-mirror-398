from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


def configure_telemetry(
    service_name: str = "phantomfetch", exporter: str = "console"
) -> None:
    """
    Configure OpenTelemetry for PhantomFetch.

    Args:
        service_name: Name of the service (default: phantomfetch)
        exporter: "console" or "none" (default: console)
    """
    resource = Resource.create(
        attributes={
            "service.name": service_name,
        }
    )

    provider = TracerProvider(resource=resource)

    if exporter == "console":
        # Use SimpleSpanProcessor for immediate output (not batched)
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def get_tracer() -> trace.Tracer:
    """Get the phantomfetch tracer."""
    return trace.get_tracer("phantomfetch")
