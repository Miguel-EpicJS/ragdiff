import pytest

from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import ChunkRevision, DocumentRevision


def test_document_and_chunk_revisions_preserve_lineage() -> None:
    document = DocumentRevision(Identifier("doc-1"), Identifier("rev-1"), "hash-doc", "v1")
    chunk = ChunkRevision(Identifier("chunk-1"), document.revision_id, 0, "hash-chunk")

    assert chunk.document_revision_id == document.revision_id
    assert chunk.ordinal == 0


def test_revisions_reject_invalid_metadata() -> None:
    with pytest.raises(ValueError, match="content hash"):
        DocumentRevision(Identifier("doc-1"), Identifier("rev-1"), " ", "v1")

    with pytest.raises(ValueError, match="ordinal"):
        ChunkRevision(Identifier("chunk-1"), Identifier("rev-1"), -1, "hash")
