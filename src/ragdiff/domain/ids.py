"""Validated identifiers shared across RAGDiff domain objects."""

import re
from dataclasses import dataclass

_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


@dataclass(frozen=True, slots=True)
class Identifier:
    """Stable, non-sensitive identifier for a domain entity."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("identifier value must be a string")
        if _IDENTIFIER_PATTERN.fullmatch(self.value) is None:
            raise ValueError(
                "identifier must start with an alphanumeric character and contain only "
                "alphanumerics, '.', '_', ':', or '-'; maximum length is 128"
            )

    def __str__(self) -> str:
        return self.value


type TenantId = Identifier
type DatasetId = Identifier
type RunId = Identifier
type DocumentId = Identifier
type RevisionId = Identifier
type ChunkId = Identifier
type QueryId = Identifier
