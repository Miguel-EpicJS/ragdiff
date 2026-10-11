from typing import Any

from fastapi import Response
from fastapi.routing import APIRoute

from ragdiff.api.app import create_app


def endpoint(app: Any, path: str) -> Any:
    routes = app.routes
    return next(
        route.endpoint for route in routes if isinstance(route, APIRoute) and route.path == path
    )


def test_health_endpoint_reports_process_health() -> None:
    app = create_app()

    assert endpoint(app, "/health")() == {"status": "ok"}


def test_readiness_reports_dependency_failures() -> None:
    app = create_app({"database": lambda: False, "vector": lambda: True})
    response = Response()

    payload = endpoint(app, "/ready")(response)

    assert response.status_code == 503
    assert payload == {
        "status": "not_ready",
        "checks": {"database": False, "vector": True},
    }
