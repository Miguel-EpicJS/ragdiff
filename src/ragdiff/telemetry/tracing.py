"""OpenTelemetry setup and tenant-safe request instrumentation."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.trace import Status, StatusCode, Tracer


def configure_tracing(service_name: str, exporter: SpanExporter | None = None) -> TracerProvider:
    """Configure a process tracer provider and return it for application wiring."""
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if exporter is not None:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def instrument_app(app: FastAPI, tracer: Tracer) -> None:
    """Trace HTTP requests without recording request bodies or credentials."""

    @app.middleware("http")
    async def trace_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Any]],
    ) -> Any:
        with tracer.start_as_current_span("http.request") as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("http.request.path", request.url.path)
            try:
                response = await call_next(request)
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR))
                raise
            span.set_attribute("http.response.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            return response
