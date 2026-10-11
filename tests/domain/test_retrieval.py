import math

import pytest

from ragdiff.domain.ids import Identifier
from ragdiff.domain.retrieval import QueryRetrieval, RetrievalRun, RetrievedItem


def _run(dataset_version: str = "v1") -> RetrievalRun:
    return RetrievalRun(
        run_id=Identifier("run-1"),
        dataset_id=Identifier("dataset-1"),
        dataset_version=dataset_version,
        pipeline_version="pipeline-1",
        queries=(
            QueryRetrieval(
                query_id=Identifier("q-1"),
                items=(RetrievedItem(Identifier("chunk-1"), rank=1, score=0.9),),
            ),
        ),
    )


def test_retrieval_run_serializes_and_round_trips() -> None:
    run = _run()

    assert RetrievalRun.from_dict(run.to_dict()) == run


def test_retrieved_items_require_positive_unique_ranks() -> None:
    with pytest.raises(ValueError, match="positive"):
        RetrievedItem(Identifier("chunk-1"), rank=0)

    with pytest.raises(ValueError, match="unique"):
        QueryRetrieval(
            Identifier("q-1"),
            (
                RetrievedItem(Identifier("chunk-1"), rank=1),
                RetrievedItem(Identifier("chunk-2"), rank=1),
            ),
        )


def test_retrieved_scores_must_be_finite() -> None:
    with pytest.raises(ValueError, match="finite"):
        RetrievedItem(Identifier("chunk-1"), rank=1, score=math.inf)


def test_runs_require_compatible_dataset_identity() -> None:
    baseline = _run()
    candidate = _run(dataset_version="v2")

    assert not baseline.is_compatible_with(candidate)
    with pytest.raises(ValueError, match="same dataset"):
        baseline.require_compatible_with(candidate)
