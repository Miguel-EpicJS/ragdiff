import asyncio
from collections.abc import MutableMapping
from typing import Any

from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ragdiff.telemetry.tracing import instrument_app


def test_http_request_creates_tenant_safe_span() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    instrument_app(app, provider.get_tracer("test"))

    messages: list[MutableMapping[str, Any]] = []

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        messages.append(message)

    asyncio.run(
        app(
            {
                "type": "http",
                "asgi": {"version": "3.0", "spec_version": "2.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/health",
                "raw_path": b"/health",
                "query_string": b"",
                "headers": [],
                "client": ("test", 1),
                "server": ("test", 80),
            },
            receive,
            send,
        )
    )

    span = exporter.get_finished_spans()[0]
    assert span.name == "http.request"
    attributes = span.attributes
    assert attributes is not None
    assert attributes["http.request.method"] == "GET"
    assert attributes["http.response.status_code"] == 200
    assert messages[0]["type"] == "http.response.start"
