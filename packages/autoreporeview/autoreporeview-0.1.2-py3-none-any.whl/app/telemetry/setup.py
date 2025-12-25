"""OpenTelemetry setup and configuration."""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing and instrumentation."""
    # Get configuration from environment variables
    service_name = os.getenv("OTEL_SERVICE_NAME", "autoreporeview")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    otlp_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")

    # Ensure endpoint has the correct path for HTTP protocol
    if not otlp_endpoint.endswith("/v1/traces"):
        # Remove trailing slash if present, then add the path
        otlp_endpoint = otlp_endpoint.rstrip("/") + "/v1/traces"

    # Parse headers if provided (format: "key1=value1,key2=value2")
    headers = {}
    if otlp_headers:
        for header_pair in otlp_headers.split(","):
            if "=" in header_pair:
                key, value = header_pair.split("=", 1)
                headers[key.strip()] = value.strip()

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.1",
        }
    )

    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Set up OTLP exporter with optional headers (for Grafana Cloud auth)
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        headers=headers if headers else None,
    )

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Instrument requests library for HTTP tracing (only if explicitly enabled)
    if os.getenv("OTEL_INSTRUMENT_REQUESTS", "false").lower() == "true":
        RequestsInstrumentor().instrument()
