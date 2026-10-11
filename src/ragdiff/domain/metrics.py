"""Deterministic retrieval quality metrics."""

import math
from collections.abc import Collection, Mapping, Sequence

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


def ndcg_at_k(
    relevance_by_id: Mapping[Identifier, float],
    retrieved_items: Sequence[RetrievedItem],
    k: int,
) -> float:
    """Return graded NDCG@K; empty or zero-gain labels return ``0.0``."""
    if k < 1:
        raise ValueError("k must be positive")
    if any(not math.isfinite(value) or value < 0 for value in relevance_by_id.values()):
        raise ValueError("relevance values must be finite and non-negative")
    if not relevance_by_id:
        return 0.0

    def gain(relevance: float) -> float:
        return (2**relevance) - 1

    ideal_gains = sorted((gain(value) for value in relevance_by_id.values()), reverse=True)[:k]
    ideal_dcg = sum(value / math.log2(rank + 2) for rank, value in enumerate(ideal_gains))
    if ideal_dcg == 0:
        return 0.0

    ranked_items = sorted(
        (item for item in retrieved_items if item.rank <= k),
        key=lambda item: item.rank,
    )
    dcg = sum(
        gain(relevance_by_id.get(item.item_id, 0.0)) / math.log2(rank + 2)
        for rank, item in enumerate(ranked_items)
    )
    return dcg / ideal_dcg
