import pytest

from ragdiff.application.embeddings import EmbeddingBatch, EmbeddingProvider


class TestProvider:
    max_batch_size = 2

    def embed(self, texts: tuple[str, ...], *, model_version: str) -> EmbeddingBatch:
        return EmbeddingBatch(
            vectors=tuple((float(len(text)), 1.0) for text in texts),
            model_version=model_version,
            dimension=2,
        )


def test_embedding_provider_contract_preserves_order_and_metadata() -> None:
    provider = TestProvider()
    assert isinstance(provider, EmbeddingProvider)

    batch = provider.embed(("one", "two"), model_version="model-v1")

    assert batch.vectors == ((3.0, 1.0), (3.0, 1.0))
    assert batch.dimension == 2
    assert provider.max_batch_size == 2


def test_embedding_batch_rejects_invalid_vectors() -> None:
    with pytest.raises(ValueError, match="dimension"):
        EmbeddingBatch(((1.0,),), "model-v1", 2)

    with pytest.raises(ValueError, match="finite"):
        EmbeddingBatch(((float("inf"),),), "model-v1", 1)
