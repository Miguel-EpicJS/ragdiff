import os
from pathlib import Path

import pytest
from psycopg import connect

from ragdiff.adapters.pgvector import PgVectorStore
from ragdiff.domain.ids import Identifier

_DATABASE_URL = os.environ.get("RAGDIFF_TEST_DATABASE_URL")


@pytest.mark.skipif(_DATABASE_URL is None, reason="RAGDIFF_TEST_DATABASE_URL is not configured")
def test_pgvector_search_is_tenant_and_model_scoped() -> None:
    assert _DATABASE_URL is not None
    with connect(_DATABASE_URL) as connection:
        for migration in sorted(Path("migrations").glob("*.sql")):
            connection.execute(migration.read_text())
        connection.execute("INSERT INTO tenants (tenant_id) VALUES ('tenant-a'), ('tenant-b')")
        connection.execute(
            "INSERT INTO documents (tenant_id, document_id) "
            "VALUES ('tenant-a', 'doc-a'), ('tenant-b', 'doc-b')"
        )
        connection.execute(
            """
            INSERT INTO document_revisions
                (tenant_id, document_id, revision_id, content_hash, source_version)
            VALUES
                ('tenant-a', 'doc-a', 'rev-a', 'hash-a', 'v1'),
                ('tenant-b', 'doc-b', 'rev-b', 'hash-b', 'v1')
            """
        )
        connection.execute(
            """
            INSERT INTO chunks
                (tenant_id, chunk_id, revision_id, ordinal, content_hash, content)
            VALUES
                ('tenant-a', 'chunk-a', 'rev-a', 0, 'chunk-hash-a', 'tenant a'),
                ('tenant-b', 'chunk-b', 'rev-b', 0, 'chunk-hash-b', 'tenant b')
            """
        )
        store = PgVectorStore(connection)
        store.upsert_embedding(
            Identifier("tenant-a"), Identifier("chunk-a"), (1.0, 0.0), "model-v1"
        )
        store.upsert_embedding(
            Identifier("tenant-b"), Identifier("chunk-b"), (0.0, 1.0), "model-v1"
        )

        results = store.search(Identifier("tenant-a"), (1.0, 0.0), "model-v1", 10)

        assert [str(result.chunk_id) for result in results] == ["chunk-a"]
        assert store.search(Identifier("tenant-a"), (1.0, 0.0), "model-v2", 10) == ()
