"""Document ingestion orchestration use case."""

from collections.abc import Sequence
from typing import Any

from psycopg import Connection

from ragdiff.adapters.pgvector import PgVectorStore
from ragdiff.application.chunking import TextChunk, chunk_text
from ragdiff.application.embeddings import EmbeddingProvider
from ragdiff.domain.ids import TenantId
from ragdiff.domain.provenance import DocumentRevision


def ingest_document(
    connection: Connection[Any],
    tenant_id: TenantId,
    document: DocumentRevision,
    text: str,
    embedding_provider: EmbeddingProvider,
    embedding_model_version: str,
    max_chars: int,
    overlap: int = 0,
) -> tuple[TextChunk, ...]:
    """Idempotently persist a revision, chunks, and their embeddings."""
    chunks = chunk_text(document, text, max_chars=max_chars, overlap=overlap)
    embeddings = _embed_chunks(embedding_provider, chunks, embedding_model_version)

    with connection.transaction():
        connection.execute(
            "INSERT INTO tenants (tenant_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (str(tenant_id),),
        )
        connection.execute(
            """
            INSERT INTO documents (tenant_id, document_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (str(tenant_id), str(document.document_id)),
        )
        connection.execute(
            """
            INSERT INTO document_revisions
                (tenant_id, document_id, revision_id, content_hash, source_version)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, revision_id) DO NOTHING
            """,
            (
                str(tenant_id),
                str(document.document_id),
                str(document.revision_id),
                document.content_hash,
                document.source_version,
            ),
        )
        row = connection.execute(
            """
            SELECT content_hash FROM document_revisions
            WHERE tenant_id = %s AND revision_id = %s
            """,
            (str(tenant_id), str(document.revision_id)),
        ).fetchone()
        if row is None or row[0] != document.content_hash:
            raise ValueError("document revision identity already exists with different content")

        for chunk in chunks:
            connection.execute(
                """
                INSERT INTO chunks
                    (tenant_id, chunk_id, revision_id, ordinal, content_hash, content)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    str(tenant_id),
                    str(chunk.revision.chunk_id),
                    str(document.revision_id),
                    chunk.revision.ordinal,
                    chunk.revision.content_hash,
                    chunk.text,
                ),
            )

        vector_store = PgVectorStore(connection)
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            vector_store.upsert_embedding(
                tenant_id,
                chunk.revision.chunk_id,
                embedding,
                embedding_model_version,
            )
    return chunks


def _embed_chunks(
    provider: EmbeddingProvider,
    chunks: Sequence[TextChunk],
    model_version: str,
) -> tuple[tuple[float, ...], ...]:
    if provider.max_batch_size < 1:
        raise ValueError("embedding provider max_batch_size must be positive")
    vectors: list[tuple[float, ...]] = []
    for start in range(0, len(chunks), provider.max_batch_size):
        batch = provider.embed(
            tuple(chunk.text for chunk in chunks[start : start + provider.max_batch_size]),
            model_version=model_version,
        )
        if len(batch.vectors) != len(chunks[start : start + provider.max_batch_size]):
            raise ValueError("embedding provider returned an unexpected vector count")
        vectors.extend(batch.vectors)
    return tuple(vectors)
