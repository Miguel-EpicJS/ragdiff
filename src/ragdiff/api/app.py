"""FastAPI service shell with health, readiness, and ingestion contracts."""

from collections.abc import Callable, Mapping
from typing import Any

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse
from psycopg import Connection
from pydantic import BaseModel, Field

from ragdiff.application.auth import (
    AuthenticatedPrincipal,
    AuthenticationError,
    BearerAuthenticator,
)
from ragdiff.application.embeddings import EmbeddingProvider
from ragdiff.application.ingestion import ingest_document
from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import DocumentRevision

ReadinessCheck = Callable[[], bool]


class DocumentIngestRequest(BaseModel):
    """Validated request for one supported plain-text document revision."""

    document_id: str
    revision_id: str
    content_hash: str
    source_version: str
    text: str
    embedding_model_version: str
    max_chars: int = Field(gt=0)
    overlap: int = Field(default=0, ge=0)


class DocumentIngestResponse(BaseModel):
    """Stable response for an accepted ingestion operation."""

    document_id: str
    revision_id: str
    chunk_count: int


def create_app(
    readiness_checks: Mapping[str, ReadinessCheck] | None = None,
    *,
    authenticator: BearerAuthenticator | None = None,
    connection: Connection[Any] | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> FastAPI:
    """Create an API app with dependency-aware readiness and ingestion."""
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

    @app.post("/v1/documents", response_model=DocumentIngestResponse, status_code=201)
    def ingest(
        payload: DocumentIngestRequest,
        authorization: str | None = Header(default=None),
    ) -> DocumentIngestResponse:
        if authenticator is None or connection is None or embedding_provider is None:
            raise RuntimeError("ingestion service is not configured")
        principal: AuthenticatedPrincipal = authenticator.authenticate(authorization)
        document = DocumentRevision(
            document_id=Identifier(payload.document_id),
            revision_id=Identifier(payload.revision_id),
            content_hash=payload.content_hash,
            source_version=payload.source_version,
        )
        chunks = ingest_document(
            connection,
            principal,
            document,
            payload.text,
            embedding_provider,
            payload.embedding_model_version,
            payload.max_chars,
            payload.overlap,
        )
        return DocumentIngestResponse(
            document_id=str(document.document_id),
            revision_id=str(document.revision_id),
            chunk_count=len(chunks),
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_failure(_request: Request, _exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "authentication_required",
                    "message": "authentication failed",
                }
            },
        )

    @app.exception_handler(RuntimeError)
    async def service_failure(_request: Request, exc: RuntimeError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "service_unavailable", "message": str(exc)}},
        )

    @app.exception_handler(ValueError)
    async def invalid_request(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "invalid_request", "message": str(exc)}},
        )

    return app
