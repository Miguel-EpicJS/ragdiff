"""Immutable document and chunk provenance contracts."""

from dataclasses import dataclass

from ragdiff.domain.ids import ChunkId, DocumentId, RevisionId


@dataclass(frozen=True, slots=True)
class DocumentRevision:
    """One immutable version of a source document."""

    document_id: DocumentId
    revision_id: RevisionId
    content_hash: str
    source_version: str

    def __post_init__(self) -> None:
        _require_non_empty(self.content_hash, "content hash")
        _require_non_empty(self.source_version, "source version")


@dataclass(frozen=True, slots=True)
class ChunkRevision:
    """One deterministic chunk derived from a document revision."""

    chunk_id: ChunkId
    document_revision_id: RevisionId
    ordinal: int
    content_hash: str

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ValueError("chunk ordinal must be non-negative")
        _require_non_empty(self.content_hash, "chunk content hash")


def _require_non_empty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{field} must be a non-empty trimmed string")
