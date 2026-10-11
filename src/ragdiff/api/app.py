"""FastAPI service shell with health and readiness contracts."""

from collections.abc import Callable, Mapping
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

ReadinessCheck = Callable[[], bool]


def create_app(readiness_checks: Mapping[str, ReadinessCheck] | None = None) -> FastAPI:
    """Create an API app with dependency-aware readiness reporting."""
    checks = dict(readiness_checks or {})
    app = FastAPI(title="RAGDiff", version="0.1.0.dev0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready(response: Response) -> dict[str, Any]:
        results: dict[str, bool] = {}
        for name, check in checks.items():
            try:
                results[name] = bool(check())
            except Exception:
                results[name] = False
        is_ready = all(results.values())
        if not is_ready:
            response.status_code = 503
        return {"status": "ready" if is_ready else "not_ready", "checks": results}

    @app.exception_handler(ValueError)
    async def invalid_request(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "invalid_request", "message": str(exc)}},
        )

    return app
