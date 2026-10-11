import os
from collections.abc import Sequence
from pathlib import Path

import pytest
from psycopg import connect

from ragdiff.application.embeddings import EmbeddingBatch
from ragdiff.application.ingestion import ingest_document
from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import DocumentRevision

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
def test_ingestion_is_idempotent_and_persists_lineage() -> None:
    assert _DATABASE_URL is not None
    with connect(_DATABASE_URL) as connection:
        for migration in sorted(Path("migrations").glob("*.sql")):
            connection.execute(migration.read_text())
        document = DocumentRevision(Identifier("doc-1"), Identifier("rev-1"), "document-hash", "v1")
        provider = FakeEmbeddingProvider()

        first = ingest_document(
            connection,
            Identifier("tenant-a"),
            document,
            "abcdefghij",
            provider,
            "model-v1",
            max_chars=4,
            overlap=1,
        )
        second = ingest_document(
            connection,
            Identifier("tenant-a"),
            document,
            "abcdefghij",
            provider,
            "model-v1",
            max_chars=4,
            overlap=1,
        )

        assert first == second
        chunk_count = connection.execute(
            "SELECT count(*) FROM chunks WHERE tenant_id = 'tenant-a'"
        ).fetchone()
        embedding_count = connection.execute(
            "SELECT count(*) FROM chunks WHERE embedding IS NOT NULL"
        ).fetchone()
        assert chunk_count is not None
        assert embedding_count is not None
        assert chunk_count[0] == 3
        assert embedding_count[0] == 3
