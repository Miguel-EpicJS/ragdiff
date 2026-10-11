import pytest

from ragdiff.domain.ids import Identifier
from ragdiff.domain.metrics import recall_at_k
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
