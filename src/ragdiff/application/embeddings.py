"""Provider-neutral embedding contracts."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class EmbeddingError(RuntimeError):
    """Base error for embedding-provider failures."""


@dataclass(frozen=True, slots=True)
class EmbeddingBatch:
    """Vectors and metadata returned for one ordered batch of texts."""

    vectors: tuple[tuple[float, ...], ...]
    model_version: str
    dimension: int

    def __post_init__(self) -> None:
        if not self.model_version or self.model_version.strip() != self.model_version:
            raise ValueError("embedding model version must be a non-empty trimmed string")
        if self.dimension < 1:
            raise ValueError("embedding dimension must be positive")
        if any(len(vector) != self.dimension for vector in self.vectors):
            raise ValueError("all embedding vectors must match the declared dimension")
        if any(not math.isfinite(value) for vector in self.vectors for value in vector):
            raise ValueError("embedding vector values must be finite")


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Port implemented by a concrete embedding provider adapter."""

    @property
    def max_batch_size(self) -> int:
        """Maximum number of texts accepted by one provider call."""
        ...

    def embed(self, texts: Sequence[str], *, model_version: str) -> EmbeddingBatch:
        """Embed texts in input order or raise ``EmbeddingError``."""
        ...
