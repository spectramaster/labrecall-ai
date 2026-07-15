import math

from labrecall.embeddings import HashEmbedder


def test_hash_embeddings_are_deterministic_and_normalized() -> None:
    embedder = HashEmbedder(64)
    first = embedder.embed("worker lost during checkpoint")
    second = embedder.embed("worker lost during checkpoint")
    assert first == second
    assert math.isclose(sum(value * value for value in first), 1.0)
