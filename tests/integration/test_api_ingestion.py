import os
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from psycopg import connect

from ragdiff.api.app import DocumentIngestRequest, create_app
from ragdiff.application.auth import AuthenticatedPrincipal, BearerAuthenticator, TokenRecord
from ragdiff.application.embeddings import EmbeddingBatch
from ragdiff.domain.ids import Identifier

_DATABASE_URL = os.environ.get("RAGDIFF_TEST_DATABASE_URL")


class FakeEmbeddingProvider:
    max_batch_size = 2

    def embed(self, texts: Sequence[str], *, model_version: str) -> EmbeddingBatch:
        return EmbeddingBatch(
            vectors=tuple((float(len(text)), 1.0) for text in texts),
            model_version=model_version,
            dimension=2,
        )


@pytest.mark.skipif(_DATABASE_URL is None, reason="RAGDIFF_TEST_DATABASE_URL is not configured")
def test_authenticated_ingestion_endpoint_persists_document() -> None:
    assert _DATABASE_URL is not None
    with connect(_DATABASE_URL) as connection:
        for migration in sorted(Path("migrations").glob("*.sql")):
            connection.execute(migration.read_text())
        principal = AuthenticatedPrincipal("user-1", Identifier("tenant-a"), frozenset())
        authenticator = BearerAuthenticator(
            {"secret-token": TokenRecord(principal, datetime.now(UTC) + timedelta(minutes=5))}
        )
        app = create_app(
            authenticator=authenticator,
            connection=connection,
            embedding_provider=FakeEmbeddingProvider(),
        )
        endpoint = next(
            route.endpoint
            for route in app.routes
            if isinstance(route, APIRoute) and route.path == "/v1/documents"
        )

        response = endpoint(
            DocumentIngestRequest(
                document_id="doc-api",
                revision_id="rev-api",
                content_hash="hash-api",
                source_version="v1",
                text="api document",
                embedding_model_version="model-v1",
                max_chars=8,
            ),
            "Bearer secret-token",
        )

        assert response.chunk_count == 2
        document_count = connection.execute(
            "SELECT count(*) FROM documents WHERE tenant_id = 'tenant-a'"
        ).fetchone()
        assert document_count is not None
        assert document_count[0] == 1
