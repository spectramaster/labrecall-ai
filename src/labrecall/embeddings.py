import hashlib
import json
import math
import re
from typing import Protocol


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    """Deterministic offline embedding used only for tests and fixture demonstrations."""

    def __init__(self, dimensions: int = 1024) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        features = [(token, 1.0) for token in tokens]
        features.extend(
            (f"{left}::{right}", 1.5)
            for left, right in zip(tokens, tokens[1:], strict=False)
        )
        for feature, weight in features:
            digest = hashlib.sha256(feature.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign * weight
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
