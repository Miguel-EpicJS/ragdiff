"""Evidence-backed source-to-query attribution."""

from dataclasses import dataclass
from typing import Literal

from ragdiff.domain.comparison import QueryComparison
from ragdiff.domain.ids import ChunkId, QueryId, RevisionId
from ragdiff.domain.provenance import ChunkRevision

AttributionConfidence = Literal["plausible", "inconclusive"]


@dataclass(frozen=True, slots=True)
class AttributionFinding:
    """A qualified provenance hypothesis for one retrieval regression."""

    query_id: QueryId
    revision_id: RevisionId | None
    affected_chunk_ids: tuple[ChunkId, ...]
    confidence: AttributionConfidence
    explanation: str


def attribute_regressions(
    comparisons: tuple[QueryComparison, ...],
    chunks: tuple[ChunkRevision, ...],
) -> tuple[AttributionFinding, ...]:
    """Map changed retrieved chunks to revisions without claiming causation."""
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    findings: list[AttributionFinding] = []
    for comparison in comparisons:
        if comparison.status != "regression":
            continue
        changed_ids = (
            set(comparison.added_item_ids)
            | set(comparison.removed_item_ids)
            | {change.item_id for change in comparison.rank_changes}
        )
        known_chunks = tuple(
            sorted(
                (chunks_by_id[chunk_id] for chunk_id in changed_ids if chunk_id in chunks_by_id),
                key=lambda chunk: str(chunk.chunk_id),
            )
        )
        if not known_chunks:
            findings.append(
                AttributionFinding(
                    query_id=comparison.query_id,
                    revision_id=None,
                    affected_chunk_ids=(),
                    confidence="inconclusive",
                    explanation="retrieval regression has no matching chunk provenance",
                )
            )
            continue

        revision_ids = {chunk.document_revision_id for chunk in known_chunks}
        for revision_id in sorted(revision_ids, key=str):
            affected = tuple(
                chunk.chunk_id
                for chunk in known_chunks
                if chunk.document_revision_id == revision_id
            )
            findings.append(
                AttributionFinding(
                    query_id=comparison.query_id,
                    revision_id=revision_id,
                    affected_chunk_ids=affected,
                    confidence="plausible",
                    explanation=(
                        "changed retrieved chunks are linked to this document revision; "
                        "the evidence does not prove causation"
                    ),
                )
            )
    return tuple(findings)
