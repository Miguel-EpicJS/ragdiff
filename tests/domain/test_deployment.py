import pytest

from ragdiff.domain.comparison import QueryComparison, QueryStatus
from ragdiff.domain.deployment import DeploymentPolicy
from ragdiff.domain.ids import Identifier
from ragdiff.domain.report import ComparisonResult


def _report(*queries: QueryComparison) -> ComparisonResult:
    return ComparisonResult(
        dataset_id=Identifier("dataset-1"),
        dataset_version="v1",
        baseline_run_id=Identifier("baseline"),
        candidate_run_id=Identifier("candidate"),
        k=10,
        queries=queries,
    )


def _query(status: QueryStatus, delta: float | None) -> QueryComparison:
    return QueryComparison(
        query_id=Identifier("q-1"),
        status=status,
        baseline_recall=1.0 if delta is not None else None,
        candidate_recall=1.0 + delta if delta is not None else None,
        recall_delta=delta,
        added_item_ids=(),
        removed_item_ids=(),
        rank_changes=(),
    )


def test_policy_allows_clean_report() -> None:
    decision = DeploymentPolicy().evaluate(_report(_query("unchanged", 0.0)))

    assert decision.allowed
    assert decision.reasons == ()


def test_policy_blocks_regressions_and_incomplete_reports() -> None:
    decision = DeploymentPolicy().evaluate(
        _report(_query("regression", -0.25), _query("incomplete", None))
    )

    assert decision.status == "blocked"
    assert decision.reasons == (
        "incomplete_queries=1",
        "regressions=1 exceeds max=0",
        "query=q-1 recall_delta=-0.250000",
    )


def test_policy_can_allow_configured_small_regression() -> None:
    decision = DeploymentPolicy(max_regressions=1, max_recall_drop=0.1).evaluate(
        _report(_query("regression", -0.05))
    )

    assert decision.allowed


def test_policy_rejects_negative_thresholds() -> None:
    with pytest.raises(ValueError, match="max_regressions"):
        DeploymentPolicy(max_regressions=-1)
    with pytest.raises(ValueError, match="max_recall_drop"):
        DeploymentPolicy(max_recall_drop=-0.1)
