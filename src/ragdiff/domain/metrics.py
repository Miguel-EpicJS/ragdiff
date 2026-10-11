"""Deterministic retrieval quality metrics."""

from collections.abc import Collection, Sequence

from ragdiff.domain.ids import Identifier
from ragdiff.domain.retrieval import RetrievedItem


def recall_at_k(
    relevant_ids: Collection[Identifier],
    retrieved_items: Sequence[RetrievedItem],
    k: int,
) -> float:
    """Return the fraction of relevant IDs retrieved in the first ``k`` items.

    A query with no labeled relevant IDs returns ``0.0`` because it provides no
    positive evidence of retrieval quality and must not appear as a success.
    """
    if k < 1:
        raise ValueError("k must be positive")
    if not relevant_ids:
        return 0.0

    retrieved_ids = {item.item_id for item in retrieved_items if item.rank <= k}
    return len(retrieved_ids & set(relevant_ids)) / len(relevant_ids)
