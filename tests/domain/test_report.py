import pytest

from ragdiff.domain.comparison import QueryComparison, RankChange
from ragdiff.domain.ids import Identifier
from ragdiff.domain.report import ComparisonResult


def test_comparison_result_round_trips_and_summarizes() -> None:
    result = ComparisonResult(
        dataset_id=Identifier("dataset-1"),
        dataset_version="v1",
        baseline_run_id=Identifier("baseline"),
        candidate_run_id=Identifier("candidate"),
        k=10,
        queries=(
            QueryComparison(
                query_id=Identifier("q-1"),
                status="regression",
                baseline_recall=1.0,
                candidate_recall=0.0,
                recall_delta=-1.0,
                added_item_ids=(Identifier("other"),),
                removed_item_ids=(Identifier("relevant"),),
                rank_changes=(RankChange(Identifier("shared"), 1, 2),),
            ),
        ),
    )

    payload = result.to_dict()
    restored = ComparisonResult.from_dict(payload)

    assert result.summary == {"regressions": 1, "improvements": 0, "unchanged": 0, "incomplete": 0}
    assert payload["summary"] == result.summary
    assert restored == result


def test_comparison_result_rejects_unknown_schema_version() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        ComparisonResult.from_dict({"schema_version": 2, "queries": []})
