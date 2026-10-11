"""PostgreSQL/pgvector chunk embedding adapter."""

from dataclasses import dataclass
from typing import Any

from psycopg import Connection

from ragdiff.domain.ids import ChunkId, Identifier, TenantId

_VECTOR_DIMENSION = 2


@dataclass(frozen=True, slots=True)
class VectorSearchResult:
    """A tenant-scoped chunk returned by vector similarity search."""

    chunk_id: ChunkId
    similarity: float


class PgVectorStore:
    """Persist and search one fixed-dimension embedding space."""

    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def upsert_embedding(
        self,
        tenant_id: TenantId,
        chunk_id: ChunkId,
        embedding: tuple[float, ...],
        model_version: str,
    ) -> None:
        _validate_embedding(embedding)
        if not model_version or model_version.strip() != model_version:
            raise ValueError("embedding model version must be a non-empty trimmed string")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chunks
                SET embedding = %s::vector, embedding_model_version = %s
                WHERE tenant_id = %s AND chunk_id = %s
                """,
                (_vector_literal(embedding), model_version, str(tenant_id), str(chunk_id)),
            )
            if cursor.rowcount != 1:
                raise LookupError("chunk does not exist for the requested tenant")

    def search(
        self,
        tenant_id: TenantId,
        query_embedding: tuple[float, ...],
        model_version: str,
        limit: int,
    ) -> tuple[VectorSearchResult, ...]:
        _validate_embedding(query_embedding)
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._connection.cursor() as cursor:
            vector = _vector_literal(query_embedding)
            cursor.execute(
                """
                SELECT chunk_id, 1 - (embedding <=> %s::vector) AS similarity
                FROM chunks
                WHERE tenant_id = %s
                  AND embedding_model_version = %s
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector, str(tenant_id), model_version, vector, limit),
            )
            return tuple(
                VectorSearchResult(Identifier(str(chunk_id)), float(similarity))
                for chunk_id, similarity in cursor.fetchall()
            )


def _validate_embedding(embedding: tuple[float, ...]) -> None:
    if len(embedding) != _VECTOR_DIMENSION:
        raise ValueError(f"embedding dimension must be {_VECTOR_DIMENSION}")


def _vector_literal(embedding: tuple[float, ...]) -> str:
    return "[" + ",".join(format(value, ".17g") for value in embedding) + "]"
