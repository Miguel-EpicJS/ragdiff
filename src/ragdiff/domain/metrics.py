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


def mean_reciprocal_rank(
    relevant_ids_by_query: Sequence[Collection[Identifier]],
    retrieved_by_query: Sequence[Sequence[RetrievedItem]],
) -> float:
    """Return mean reciprocal rank across queries.

    Queries without a relevant retrieved item contribute ``0.0``. An empty
    query collection returns ``0.0``.
    """
    if len(relevant_ids_by_query) != len(retrieved_by_query):
        raise ValueError("relevance and retrieval query collections must have equal length")
    if not relevant_ids_by_query:
        return 0.0

    reciprocal_ranks: list[float] = []
    for relevant_ids, retrieved_items in zip(
        relevant_ids_by_query, retrieved_by_query, strict=True
    ):
        relevant_ranks = [item.rank for item in retrieved_items if item.item_id in relevant_ids]
        reciprocal_ranks.append(1.0 / min(relevant_ranks) if relevant_ranks else 0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)
