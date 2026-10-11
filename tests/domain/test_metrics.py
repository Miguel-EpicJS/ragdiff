import pytest

from ragdiff.domain.ids import Identifier
from ragdiff.domain.metrics import mean_reciprocal_rank, ndcg_at_k, recall_at_k
from ragdiff.domain.retrieval import RetrievedItem


def item(item_id: str, rank: int) -> RetrievedItem:
    return RetrievedItem(Identifier(item_id), rank=rank)


def test_recall_at_k_counts_relevant_items_within_cutoff() -> None:
    relevant = {Identifier("chunk-1"), Identifier("chunk-2")}

    assert recall_at_k(relevant, (item("chunk-1", 1), item("other", 2)), 2) == 0.5
    assert recall_at_k(relevant, (item("chunk-1", 1), item("chunk-2", 2)), 1) == 0.5


def test_recall_at_k_returns_zero_for_empty_relevance_set() -> None:
    assert recall_at_k(set(), (item("chunk-1", 1),), 1) == 0.0


def test_recall_at_k_rejects_non_positive_cutoff() -> None:
    with pytest.raises(ValueError, match="positive"):
        recall_at_k({Identifier("chunk-1")}, (), 0)


def test_mean_reciprocal_rank_uses_first_relevant_rank() -> None:
    relevant = [{Identifier("chunk-1")}, {Identifier("chunk-2")}]
    retrieved = [
        (item("other", 1), item("chunk-1", 2)),
        (item("other", 1),),
    ]

    assert mean_reciprocal_rank(relevant, retrieved) == 0.25


def test_mean_reciprocal_rank_handles_empty_and_mismatched_inputs() -> None:
    assert mean_reciprocal_rank([], []) == 0.0

    with pytest.raises(ValueError, match="equal length"):
        mean_reciprocal_rank([{Identifier("chunk-1")}], [])


def test_ndcg_at_k_rewards_correct_ordering() -> None:
    relevance = {Identifier("chunk-1"): 3.0, Identifier("chunk-2"): 2.0}

    assert ndcg_at_k(relevance, (item("chunk-1", 1), item("chunk-2", 2)), 2) == pytest.approx(1.0)
    assert ndcg_at_k(relevance, (item("chunk-2", 1), item("chunk-1", 2)), 2) < 1.0


def test_ndcg_at_k_handles_empty_and_invalid_relevance() -> None:
    assert ndcg_at_k({}, (), 1) == 0.0

    with pytest.raises(ValueError, match="non-negative"):
        ndcg_at_k({Identifier("chunk-1"): -1.0}, (), 1)

    with pytest.raises(ValueError, match="positive"):
        ndcg_at_k({}, (), 0)
