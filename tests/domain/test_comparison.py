import pytest

from ragdiff.domain.comparison import compare_runs
from ragdiff.domain.dataset import EvaluationDataset, EvaluationQuery
from ragdiff.domain.ids import Identifier
from ragdiff.domain.retrieval import QueryRetrieval, RetrievalRun, RetrievedItem


def test_compare_runs_reports_regressions_improvements_and_missing_queries() -> None:
    dataset = EvaluationDataset(
        Identifier("dataset-1"),
        "v1",
        (
            EvaluationQuery(Identifier("q-regression"), frozenset({Identifier("chunk-a")})),
            EvaluationQuery(Identifier("q-improvement"), frozenset({Identifier("chunk-b")})),
            EvaluationQuery(Identifier("q-missing"), frozenset({Identifier("chunk-c")})),
        ),
    )
    baseline = RetrievalRun(
        Identifier("baseline"),
        Identifier("dataset-1"),
        "v1",
        "pipeline-old",
        (
            QueryRetrieval(
                Identifier("q-regression"),
                (RetrievedItem(Identifier("chunk-a"), 1),),
            ),
            QueryRetrieval(
                Identifier("q-improvement"),
                (RetrievedItem(Identifier("other"), 1),),
            ),
        ),
    )
    candidate = RetrievalRun(
        Identifier("candidate"),
        Identifier("dataset-1"),
        "v1",
        "pipeline-new",
        (
            QueryRetrieval(
                Identifier("q-regression"),
                (RetrievedItem(Identifier("other"), 1),),
            ),
            QueryRetrieval(
                Identifier("q-improvement"),
                (RetrievedItem(Identifier("chunk-b"), 1),),
            ),
        ),
    )

    comparisons = compare_runs(dataset, baseline, candidate, k=1)

    assert [comparison.status for comparison in comparisons] == [
        "regression",
        "improvement",
        "incomplete",
    ]
    assert comparisons[0].removed_item_ids == (Identifier("chunk-a"),)
    assert comparisons[1].added_item_ids == (Identifier("chunk-b"),)


def test_compare_runs_reports_rank_changes_and_rejects_wrong_dataset() -> None:
    dataset = EvaluationDataset(
        Identifier("dataset-1"),
        "v1",
        (EvaluationQuery(Identifier("q-1"), frozenset({Identifier("chunk-a")})),),
    )
    baseline = RetrievalRun(
        Identifier("baseline"),
        Identifier("dataset-1"),
        "v1",
        "old",
        (QueryRetrieval(Identifier("q-1"), (RetrievedItem(Identifier("chunk-a"), 1),)),),
    )
    candidate = RetrievalRun(
        Identifier("candidate"),
        Identifier("dataset-1"),
        "v1",
        "new",
        (QueryRetrieval(Identifier("q-1"), (RetrievedItem(Identifier("chunk-a"), 2),)),),
    )

    comparison = compare_runs(dataset, baseline, candidate, k=2)[0]

    assert comparison.status == "unchanged"
    assert comparison.rank_changes[0].baseline_rank == 1
    assert comparison.rank_changes[0].candidate_rank == 2

    wrong_dataset = EvaluationDataset(Identifier("other-dataset"), "v1", dataset.queries)
    with pytest.raises(ValueError, match="match the evaluation dataset"):
        compare_runs(wrong_dataset, baseline, candidate, k=1)
