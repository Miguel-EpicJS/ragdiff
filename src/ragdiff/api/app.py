"""FastAPI service shell with health, ingestion, and comparison contracts."""

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from opentelemetry import trace
from opentelemetry.trace import Tracer
from psycopg import Connection
from pydantic import BaseModel, Field

from ragdiff.application.auth import (
    AuthenticatedPrincipal,
    AuthenticationError,
    BearerAuthenticator,
)
from ragdiff.application.embeddings import EmbeddingProvider
from ragdiff.application.ingestion import ingest_document
from ragdiff.domain.comparison import compare_runs
from ragdiff.domain.dataset import EvaluationDataset
from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import DocumentRevision
from ragdiff.domain.report import ComparisonResult
from ragdiff.domain.retrieval import RetrievalRun
from ragdiff.telemetry.tracing import instrument_app

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


class ComparisonRequest(BaseModel):
    """Baseline/candidate comparison input."""

    report_id: str
    dataset: dict[str, Any]
    baseline: dict[str, Any]
    candidate: dict[str, Any]
    k: int = Field(gt=0)


class ComparisonResponse(BaseModel):
    """Persisted comparison report and provisional deployment decision."""

    report_id: str
    deployment_status: str
    result: dict[str, Any]


def create_app(
    readiness_checks: Mapping[str, ReadinessCheck] | None = None,
    *,
    authenticator: BearerAuthenticator | None = None,
    connection: Connection[Any] | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    tracer: Tracer | None = None,
) -> FastAPI:
    """Create an API app with dependency-aware product workflows."""
    checks = dict(readiness_checks or {})
    app = FastAPI(title="RAGDiff", version="0.1.0.dev0")
    if Path("frontend").is_dir():
        app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")
    if tracer is not None:
        instrument_app(app, tracer)

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
        trace.get_current_span().set_attribute("ragdiff.tenant_id", str(principal.tenant_id))
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

    @app.post("/v1/comparisons", response_model=ComparisonResponse, status_code=201)
    def compare(
        payload: ComparisonRequest,
        authorization: str | None = Header(default=None),
    ) -> ComparisonResponse:
        if authenticator is None or connection is None:
            raise RuntimeError("comparison service is not configured")
        principal = authenticator.authenticate(authorization)
        trace.get_current_span().set_attribute("ragdiff.tenant_id", str(principal.tenant_id))
        dataset = EvaluationDataset.from_dict(payload.dataset)
        baseline = RetrievalRun.from_dict(payload.baseline)
        candidate = RetrievalRun.from_dict(payload.candidate)
        comparisons = compare_runs(dataset, baseline, candidate, payload.k)
        report = ComparisonResult(
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            baseline_run_id=baseline.run_id,
            candidate_run_id=candidate.run_id,
            k=payload.k,
            queries=comparisons,
        )
        deployment_status = "blocked" if report.summary["regressions"] else "allowed"
        result = {"comparison": report.to_dict(), "deployment_status": deployment_status}
        connection.execute(
            """
            INSERT INTO comparison_reports
                (tenant_id, report_id, dataset_id, dataset_version,
                 baseline_run_id, candidate_run_id, cutoff_k, result)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (tenant_id, report_id) DO UPDATE SET result = EXCLUDED.result
            """,
            (
                str(principal.tenant_id),
                payload.report_id,
                str(dataset.dataset_id),
                dataset.version,
                str(baseline.run_id),
                str(candidate.run_id),
                payload.k,
                json.dumps(result),
            ),
        )
        connection.commit()
        return ComparisonResponse(
            report_id=payload.report_id,
            deployment_status=deployment_status,
            result=result,
        )

    @app.get("/v1/comparisons/{report_id}", response_model=ComparisonResponse)
    def get_comparison(
        report_id: str,
        authorization: str | None = Header(default=None),
    ) -> ComparisonResponse:
        if authenticator is None or connection is None:
            raise RuntimeError("comparison service is not configured")
        principal = authenticator.authenticate(authorization)
        trace.get_current_span().set_attribute("ragdiff.tenant_id", str(principal.tenant_id))
        row = connection.execute(
            """
            SELECT result FROM comparison_reports
            WHERE tenant_id = %s AND report_id = %s
            """,
            (str(principal.tenant_id), report_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="comparison report not found")
        result = row[0]
        return ComparisonResponse(
            report_id=report_id,
            deployment_status=result["deployment_status"],
            result=result,
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
