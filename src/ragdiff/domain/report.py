"""Versioned machine-readable comparison reports."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ragdiff.domain.comparison import QueryComparison, RankChange
from ragdiff.domain.ids import DatasetId, Identifier, RunId

_SCHEMA_VERSION = 1
_VALID_STATUSES = {"regression", "improvement", "unchanged", "incomplete"}


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Serializable report for one baseline/candidate comparison."""

    dataset_id: DatasetId
    dataset_version: str
    baseline_run_id: RunId
    candidate_run_id: RunId
    k: int
    queries: tuple[QueryComparison, ...]

    def __post_init__(self) -> None:
        if self.k < 1:
            raise ValueError("k must be positive")
        if not self.dataset_version or self.dataset_version.strip() != self.dataset_version:
            raise ValueError("dataset version must be a non-empty trimmed string")

    @property
    def summary(self) -> dict[str, int]:
        return {
            "regressions": sum(query.status == "regression" for query in self.queries),
            "improvements": sum(query.status == "improvement" for query in self.queries),
            "unchanged": sum(query.status == "unchanged" for query in self.queries),
            "incomplete": sum(query.status == "incomplete" for query in self.queries),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "dataset_id": str(self.dataset_id),
            "dataset_version": self.dataset_version,
            "baseline_run_id": str(self.baseline_run_id),
            "candidate_run_id": str(self.candidate_run_id),
            "k": self.k,
            "summary": self.summary,
            "queries": [_query_to_dict(query) for query in self.queries],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComparisonResult":
        if payload.get("schema_version") != _SCHEMA_VERSION:
            version = payload.get("schema_version")
            raise ValueError(f"unsupported comparison schema version: {version!r}")
        raw_queries = payload.get("queries")
        if not isinstance(raw_queries, list):
            raise ValueError("comparison queries must be a list")
        return cls(
            dataset_id=Identifier(_required_string(payload, "dataset_id")),
            dataset_version=_required_string(payload, "dataset_version"),
            baseline_run_id=Identifier(_required_string(payload, "baseline_run_id")),
            candidate_run_id=Identifier(_required_string(payload, "candidate_run_id")),
            k=_required_int(payload, "k"),
            queries=tuple(_query_from_dict(value) for value in raw_queries),
        )


def _query_to_dict(query: QueryComparison) -> dict[str, Any]:
    return {
        "query_id": str(query.query_id),
        "status": query.status,
        "baseline_recall": query.baseline_recall,
        "candidate_recall": query.candidate_recall,
        "recall_delta": query.recall_delta,
        "added_item_ids": [str(item_id) for item_id in query.added_item_ids],
        "removed_item_ids": [str(item_id) for item_id in query.removed_item_ids],
        "rank_changes": [
            {
                "item_id": str(change.item_id),
                "baseline_rank": change.baseline_rank,
                "candidate_rank": change.candidate_rank,
            }
            for change in query.rank_changes
        ],
    }


def _query_from_dict(value: Any) -> QueryComparison:
    if not isinstance(value, Mapping):
        raise ValueError("each comparison query must be an object")
    status = value.get("status")
    if status not in _VALID_STATUSES:
        raise ValueError(f"unsupported query comparison status: {status!r}")
    raw_rank_changes = value.get("rank_changes")
    if not isinstance(raw_rank_changes, list):
        raise ValueError("query rank_changes must be a list")
    return QueryComparison(
        query_id=Identifier(_required_string(value, "query_id")),
        status=status,
        baseline_recall=_optional_float(value, "baseline_recall"),
        candidate_recall=_optional_float(value, "candidate_recall"),
        recall_delta=_optional_float(value, "recall_delta"),
        added_item_ids=_identifier_tuple(value, "added_item_ids"),
        removed_item_ids=_identifier_tuple(value, "removed_item_ids"),
        rank_changes=tuple(_rank_change_from_dict(change) for change in raw_rank_changes),
    )


def _rank_change_from_dict(value: Any) -> RankChange:
    if not isinstance(value, Mapping):
        raise ValueError("each rank change must be an object")
    return RankChange(
        item_id=Identifier(_required_string(value, "item_id")),
        baseline_rank=_required_int(value, "baseline_rank"),
        candidate_rank=_required_int(value, "candidate_rank"),
    )


def _identifier_tuple(payload: Mapping[str, Any], key: str) -> tuple[Identifier, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(Identifier(item) for item in value)


def _optional_float(payload: Mapping[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is not None and not isinstance(value, (float, int)):
        raise ValueError(f"{key} must be numeric or null")
    return float(value) if value is not None else None


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value
