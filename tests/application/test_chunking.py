import pytest

from ragdiff.application.chunking import chunk_text
from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import DocumentRevision


def document() -> DocumentRevision:
    return DocumentRevision(Identifier("doc-1"), Identifier("rev-1"), "doc-hash", "v1")


def test_chunking_is_deterministic_and_traceable() -> None:
    first = chunk_text(document(), "abcdefghij", max_chars=4, overlap=1)
    second = chunk_text(document(), "abcdefghij", max_chars=4, overlap=1)

    assert first == second
    assert [chunk.text for chunk in first] == ["abcd", "defg", "ghij"]
    assert all(chunk.revision.document_revision_id == Identifier("rev-1") for chunk in first)
    assert [chunk.revision.ordinal for chunk in first] == [0, 1, 2]


def test_chunking_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        chunk_text(document(), " ", max_chars=4)
    with pytest.raises(ValueError, match="positive"):
        chunk_text(document(), "text", max_chars=0)
    with pytest.raises(ValueError, match="smaller"):
        chunk_text(document(), "text", max_chars=4, overlap=4)
