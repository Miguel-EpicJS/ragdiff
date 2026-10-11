from ragdiff.application.attribution import attribute_regressions
from ragdiff.domain.comparison import QueryComparison, RankChange
from ragdiff.domain.ids import Identifier
from ragdiff.domain.provenance import ChunkRevision


def regression(query_id: str, chunk_id: str) -> QueryComparison:
    return QueryComparison(
        query_id=Identifier(query_id),
        status="regression",
        baseline_recall=1.0,
        candidate_recall=0.0,
        recall_delta=-1.0,
        added_item_ids=(),
        removed_item_ids=(Identifier(chunk_id),),
        rank_changes=(RankChange(Identifier(chunk_id), 1, 3),),
    )


def test_attribution_links_regressions_to_plausible_revisions() -> None:
    findings = attribute_regressions(
        (regression("q-1", "chunk-a"),),
        (ChunkRevision(Identifier("chunk-a"), Identifier("rev-a"), 0, "hash"),),
    )

    assert findings[0].revision_id == Identifier("rev-a")
    assert findings[0].confidence == "plausible"
    assert "does not prove causation" in findings[0].explanation


def test_attribution_marks_unknown_chunks_inconclusive() -> None:
    findings = attribute_regressions((regression("q-1", "unknown"),), ())

    assert findings[0].revision_id is None
    assert findings[0].confidence == "inconclusive"
