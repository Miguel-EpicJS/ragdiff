"""Typed evaluation dataset contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ragdiff.domain.ids import DatasetId, Identifier, QueryId

_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class EvaluationQuery:
    """A query and the source/chunk identifiers considered relevant."""

    query_id: QueryId
    relevant_ids: frozenset[Identifier]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": str(self.query_id),
            "relevant_ids": sorted(map(str, self.relevant_ids)),
        }


@dataclass(frozen=True, slots=True)
class EvaluationDataset:
    """Immutable, versioned set of labeled retrieval queries."""

    dataset_id: DatasetId
    version: str
    queries: tuple[EvaluationQuery, ...]

    def __post_init__(self) -> None:
        if not self.version or self.version.strip() != self.version:
            raise ValueError("dataset version must be a non-empty trimmed string")
        query_ids = [query.query_id for query in self.queries]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("dataset query IDs must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "dataset_id": str(self.dataset_id),
            "version": self.version,
            "queries": [query.to_dict() for query in self.queries],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EvaluationDataset":
        if payload.get("schema_version") != _SCHEMA_VERSION:
            version = payload.get("schema_version")
            raise ValueError(f"unsupported dataset schema version: {version!r}")

        raw_queries = payload.get("queries")
        if not isinstance(raw_queries, list):
            raise ValueError("dataset queries must be a list")

        queries: list[EvaluationQuery] = []
        for raw_query in raw_queries:
            if not isinstance(raw_query, Mapping):
                raise ValueError("each dataset query must be an object")
            raw_relevant_ids = raw_query.get("relevant_ids")
            if not isinstance(raw_relevant_ids, list):
                raise ValueError("query relevant_ids must be a list")
            queries.append(
                EvaluationQuery(
                    query_id=Identifier(_required_string(raw_query, "query_id")),
                    relevant_ids=frozenset(
                        Identifier(_required_string_value(value)) for value in raw_relevant_ids
                    ),
                )
            )

        return cls(
            dataset_id=Identifier(_required_string(payload, "dataset_id")),
            version=_required_string(payload, "version"),
            queries=tuple(queries),
        )


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    return _required_string_value(value, field=key)


def _required_string_value(value: Any, field: str = "identifier") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value
