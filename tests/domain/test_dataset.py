import pytest

from ragdiff.domain.dataset import EvaluationDataset, EvaluationQuery
from ragdiff.domain.ids import Identifier


def test_dataset_serializes_and_round_trips() -> None:
    dataset = EvaluationDataset(
        dataset_id=Identifier("support-set"),
        version="2026-10-11",
        queries=(
            EvaluationQuery(
                query_id=Identifier("q-2"),
                relevant_ids=frozenset({Identifier("chunk-b"), Identifier("chunk-a")}),
            ),
        ),
    )

    payload = dataset.to_dict()
    restored = EvaluationDataset.from_dict(payload)

    assert payload["schema_version"] == 1
    assert payload["queries"][0]["relevant_ids"] == ["chunk-a", "chunk-b"]
    assert restored == dataset


def test_dataset_rejects_duplicate_query_ids() -> None:
    query = EvaluationQuery(Identifier("q-1"), frozenset())

    with pytest.raises(ValueError, match="unique"):
        EvaluationDataset(Identifier("set"), "v1", (query, query))


def test_dataset_rejects_unsupported_schema_version() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        EvaluationDataset.from_dict(
            {"schema_version": 2, "dataset_id": "set", "version": "v1", "queries": []}
        )


def test_dataset_rejects_malformed_relevance_ids() -> None:
    with pytest.raises(ValueError, match="relevant_ids"):
        EvaluationDataset.from_dict(
            {
                "schema_version": 1,
                "dataset_id": "set",
                "version": "v1",
                "queries": [{"query_id": "q-1", "relevant_ids": "chunk-1"}],
            }
        )
