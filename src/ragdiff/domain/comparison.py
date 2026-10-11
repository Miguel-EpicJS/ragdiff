"""Baseline-versus-candidate retrieval comparison."""

from dataclasses import dataclass
from typing import Literal

from ragdiff.domain.dataset import EvaluationDataset
from ragdiff.domain.ids import Identifier, QueryId
from ragdiff.domain.metrics import recall_at_k
from ragdiff.domain.retrieval import QueryRetrieval, RetrievalRun, RetrievedItem

QueryStatus = Literal["regression", "improvement", "unchanged", "incomplete"]


@dataclass(frozen=True, slots=True)
class RankChange:
    """Rank movement for an item present in both runs."""

    item_id: Identifier
    baseline_rank: int
    candidate_rank: int


@dataclass(frozen=True, slots=True)
class QueryComparison:
    """Measured comparison for one evaluation query."""

    query_id: QueryId
    status: QueryStatus
    baseline_recall: float | None
    candidate_recall: float | None
    recall_delta: float | None
    added_item_ids: tuple[Identifier, ...]
    removed_item_ids: tuple[Identifier, ...]
    rank_changes: tuple[RankChange, ...]


def compare_runs(
    dataset: EvaluationDataset,
    baseline: RetrievalRun,
    candidate: RetrievalRun,
    k: int,
) -> tuple[QueryComparison, ...]:
    """Compare baseline and candidate retrieval outputs in dataset order."""
    if k < 1:
        raise ValueError("k must be positive")
    baseline.require_compatible_with(candidate)
    if baseline.dataset_id != dataset.dataset_id or baseline.dataset_version != dataset.version:
        raise ValueError("retrieval runs must match the evaluation dataset")

    baseline_by_query = {query.query_id: query for query in baseline.queries}
    candidate_by_query = {query.query_id: query for query in candidate.queries}
    comparisons: list[QueryComparison] = []
    for evaluation_query in dataset.queries:
        baseline_query = baseline_by_query.get(evaluation_query.query_id)
        candidate_query = candidate_by_query.get(evaluation_query.query_id)
        comparisons.append(
            _compare_query(
                evaluation_query.query_id,
                evaluation_query.relevant_ids,
                baseline_query,
                candidate_query,
                k,
            )
        )
    return tuple(comparisons)


def _compare_query(
    query_id: QueryId,
    relevant_ids: frozenset[Identifier],
    baseline: QueryRetrieval | None,
    candidate: QueryRetrieval | None,
    k: int,
) -> QueryComparison:
    baseline_items = _items_by_id(baseline)
    candidate_items = _items_by_id(candidate)
    common_ids = baseline_items.keys() & candidate_items.keys()
    rank_changes = tuple(
        RankChange(item_id, baseline_items[item_id].rank, candidate_items[item_id].rank)
        for item_id in sorted(common_ids, key=str)
        if baseline_items[item_id].rank != candidate_items[item_id].rank
    )
    added = tuple(sorted(candidate_items.keys() - baseline_items.keys(), key=str))
    removed = tuple(sorted(baseline_items.keys() - candidate_items.keys(), key=str))

    if baseline is None or candidate is None:
        return QueryComparison(
            query_id, "incomplete", None, None, None, added, removed, rank_changes
        )

    baseline_recall = recall_at_k(relevant_ids, baseline.items, k)
    candidate_recall = recall_at_k(relevant_ids, candidate.items, k)
    recall_delta = candidate_recall - baseline_recall
    status: QueryStatus
    if recall_delta < 0:
        status = "regression"
    elif recall_delta > 0:
        status = "improvement"
    else:
        status = "unchanged"
    return QueryComparison(
        query_id,
        status,
        baseline_recall,
        candidate_recall,
        recall_delta,
        added,
        removed,
        rank_changes,
    )


def _items_by_id(query: QueryRetrieval | None) -> dict[Identifier, RetrievedItem]:
    if query is None:
        return {}
    return {item.item_id: item for item in query.items}
