import hashlib
import json
import math
from typing import Protocol


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    """Deterministic offline embedding used only for tests and fixture demonstrations."""

    def __init__(self, dimensions: int = 1024) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = text.lower().split()
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class BedrockTitanEmbedder:
    def __init__(self, client: object, model_id: str, dimensions: int = 1024) -> None:
        self.client = client
        self.model_id = model_id
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": self.dimensions,
                    "normalize": True,
                }
            ),
        )
        payload = json.loads(response["body"].read())
        return [float(value) for value in payload["embedding"]]
