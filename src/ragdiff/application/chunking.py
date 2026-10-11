"""Deterministic plain-text chunking with provenance."""

import hashlib
from dataclasses import dataclass

from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import ChunkRevision, DocumentRevision


@dataclass(frozen=True, slots=True)
class TextChunk:
    """Chunk text and its immutable provenance metadata."""

    revision: ChunkRevision
    text: str


def chunk_text(
    document: DocumentRevision,
    text: str,
    max_chars: int,
    overlap: int = 0,
) -> tuple[TextChunk, ...]:
    """Split plain text into stable fixed-width chunks."""
    if not text.strip():
        raise ValueError("document text must be non-empty")
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be non-negative and smaller than max_chars")

    normalized_text = text.strip()
    step = max_chars - overlap
    chunks: list[TextChunk] = []
    for ordinal, start in enumerate(range(0, len(normalized_text), step)):
        chunk_text_value = normalized_text[start : start + max_chars]
        content_hash = hashlib.sha256(chunk_text_value.encode("utf-8")).hexdigest()
        chunk_id = Identifier(f"chunk-{content_hash[:16]}")
        chunks.append(
            TextChunk(
                revision=ChunkRevision(
                    chunk_id=chunk_id,
                    document_revision_id=document.revision_id,
                    ordinal=ordinal,
                    content_hash=content_hash,
                ),
                text=chunk_text_value,
            )
        )
        if start + max_chars >= len(normalized_text):
            break
    return tuple(chunks)
