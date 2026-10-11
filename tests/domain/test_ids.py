import pytest

from ragdiff.domain.ids import Identifier


def test_identifier_is_immutable_and_string_like() -> None:
    identifier = Identifier("dataset-v1")

    assert str(identifier) == "dataset-v1"
    assert identifier == Identifier("dataset-v1")
    assert hash(identifier) == hash(Identifier("dataset-v1"))


def test_identifier_rejects_invalid_values() -> None:
    for value in ("", " has-space", "has space", "a/b", "!invalid"):
        with pytest.raises(ValueError):
            Identifier(value)


def test_identifier_rejects_non_strings() -> None:
    with pytest.raises(TypeError):
        Identifier(123)  # type: ignore[arg-type]


def test_identifier_rejects_values_longer_than_128_characters() -> None:
    with pytest.raises(ValueError):
        Identifier("a" * 129)
