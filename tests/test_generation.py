from uuid import uuid4

from labrecall.generation import BedrockNovaExplainer
from labrecall.models import IncidentInput, RecalledMemory


class FakeBedrock:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def converse(self, **request: object) -> dict[str, object]:
        self.request = request
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": (
                                "The retrieved repair is relevant but must be verified. "
                                "Human approval remains required."
                            )
                        }
                    ]
                }
            }
        }


def test_nova_explainer_is_evidence_bounded() -> None:
    client = FakeBedrock()
    explainer = BedrockNovaExplainer(client, "amazon.nova-lite-v1:0")
    text = explainer.explain(
        IncidentInput(pipeline="calibration", error="drift detected", environment="fixture"),
        [
            RecalledMemory(
                memory_id=uuid4(),
                similarity=0.9,
                failure_signature="prior drift",
                repair_action="Acquire a fresh reference.",
                successful_outcomes=2,
                failed_outcomes=0,
                confidence=0.75,
            )
        ],
        ["Run a read-only diagnostic.", "Acquire a fresh reference."],
    )

    assert "Human approval" in text
    assert client.request is not None
    assert client.request["modelId"] == "amazon.nova-lite-v1:0"
    assert client.request["inferenceConfig"] == {"maxTokens": 180, "temperature": 0.0}


class FailingExplainer:
    def explain(self, *args: object) -> str:
        raise RuntimeError("simulated Bedrock outage")


def test_agent_falls_back_when_explainer_is_unavailable() -> None:
    from labrecall.agent import RepairAgent
    from labrecall.embeddings import HashEmbedder
    from labrecall.memory import LocalMemoryStore

    agent = RepairAgent(LocalMemoryStore(), HashEmbedder(32), explainer=FailingExplainer())
    result = agent.analyze(
        IncidentInput(pipeline="calibration", error="drift detected", environment="fixture")
    )

    assert result.generation_mode == "deterministic"
    assert result.generation_degraded is True
