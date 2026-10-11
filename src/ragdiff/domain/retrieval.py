"""Typed retrieval run contracts."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ragdiff.domain.ids import DatasetId, Identifier, QueryId, RunId

_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RetrievedItem:
    """One ranked retrieval result for a query."""

    item_id: Identifier
    rank: int
    score: float | None = None
    citation: str | None = None

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError("retrieved item rank must be positive")
        if self.score is not None and not math.isfinite(self.score):
            raise ValueError("retrieved item score must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": str(self.item_id),
            "rank": self.rank,
            "score": self.score,
            "citation": self.citation,
        }


@dataclass(frozen=True, slots=True)
class QueryRetrieval:
    """Ranked retrieval results for one evaluation query."""

    query_id: QueryId
    items: tuple[RetrievedItem, ...]

    def __post_init__(self) -> None:
        ranks = [item.rank for item in self.items]
        if len(ranks) != len(set(ranks)):
            raise ValueError("retrieved item ranks must be unique per query")

    def to_dict(self) -> dict[str, Any]:
        return {"query_id": str(self.query_id), "items": [item.to_dict() for item in self.items]}


@dataclass(frozen=True, slots=True)
class RetrievalRun:
    """Immutable retrieval output tied to one exact evaluation dataset."""

    run_id: RunId
    dataset_id: DatasetId
    dataset_version: str
    pipeline_version: str
    queries: tuple[QueryRetrieval, ...]

    def __post_init__(self) -> None:
        if not self.dataset_version or self.dataset_version.strip() != self.dataset_version:
            raise ValueError("dataset version must be a non-empty trimmed string")
        if not self.pipeline_version or self.pipeline_version.strip() != self.pipeline_version:
            raise ValueError("pipeline version must be a non-empty trimmed string")
        query_ids = [query.query_id for query in self.queries]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("retrieval run query IDs must be unique")

    def is_compatible_with(self, other: "RetrievalRun") -> bool:
        return self.dataset_id == other.dataset_id and self.dataset_version == other.dataset_version

    def require_compatible_with(self, other: "RetrievalRun") -> None:
        if not self.is_compatible_with(other):
            raise ValueError("retrieval runs must use the same dataset identity and version")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "run_id": str(self.run_id),
            "dataset_id": str(self.dataset_id),
            "dataset_version": self.dataset_version,
            "pipeline_version": self.pipeline_version,
            "queries": [query.to_dict() for query in self.queries],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RetrievalRun":
        if payload.get("schema_version") != _SCHEMA_VERSION:
            version = payload.get("schema_version")
            raise ValueError(f"unsupported retrieval run schema version: {version!r}")
        raw_queries = payload.get("queries")
        if not isinstance(raw_queries, list):
            raise ValueError("retrieval run queries must be a list")

        queries: list[QueryRetrieval] = []
        for raw_query in raw_queries:
            if not isinstance(raw_query, Mapping):
                raise ValueError("each retrieval query must be an object")
            raw_items = raw_query.get("items")
            if not isinstance(raw_items, list):
                raise ValueError("retrieval query items must be a list")
            items: list[RetrievedItem] = []
            for raw_item in raw_items:
                if not isinstance(raw_item, Mapping):
                    raise ValueError("each retrieved item must be an object")
                score = raw_item.get("score")
                if score is not None and not isinstance(score, (float, int)):
                    raise ValueError("retrieved item score must be numeric or null")
                citation = raw_item.get("citation")
                if citation is not None and not isinstance(citation, str):
                    raise ValueError("retrieved item citation must be a string or null")
                items.append(
                    RetrievedItem(
                        item_id=Identifier(_required_string(raw_item, "item_id")),
                        rank=_required_int(raw_item, "rank"),
                        score=float(score) if score is not None else None,
                        citation=citation,
                    )
                )
            queries.append(
                QueryRetrieval(
                    query_id=Identifier(_required_string(raw_query, "query_id")),
                    items=tuple(items),
                )
            )

        return cls(
            run_id=Identifier(_required_string(payload, "run_id")),
            dataset_id=Identifier(_required_string(payload, "dataset_id")),
            dataset_version=_required_string(payload, "dataset_version"),
            pipeline_version=_required_string(payload, "pipeline_version"),
            queries=tuple(queries),
        )


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
