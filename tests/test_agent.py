from labrecall.agent import RepairAgent
from labrecall.embeddings import HashEmbedder
from labrecall.memory import LocalMemoryStore
from labrecall.models import IncidentInput, OutcomeInput


def incident(error: str = "CUDA out of memory during validation") -> IncidentInput:
    return IncidentInput(
        pipeline="spectroscopy training",
        error=error,
        environment="Python 3.12, batch size 64, GPU 8 GB",
        attempted_actions=["restarted the run"],
        constraints=["do not change the validation dataset"],
    )


def test_successful_outcome_becomes_cited_memory() -> None:
    agent = RepairAgent(LocalMemoryStore(), HashEmbedder(64), retrieval_limit=3)
    first = agent.analyze(incident())
    assert first.evidence == []

    receipt = agent.learn(
        first.incident_id,
        OutcomeInput(
            status="worked",
            action_taken="Reduce validation batch size from 64 to 16.",
            observation="Validation completed with identical sample order.",
        ),
    )
    assert receipt.learned is True

    second = agent.analyze(incident("CUDA out of memory in the validation step"))
    assert second.evidence
    assert second.evidence[0].memory_id == receipt.promoted_memory_id
    assert "Reduce validation batch size" in second.proposed_actions[1]


def test_failed_outcome_is_not_promoted() -> None:
    store = LocalMemoryStore()
    agent = RepairAgent(store, HashEmbedder(64))
    recommendation = agent.analyze(incident())
    receipt = agent.learn(
        recommendation.incident_id,
        OutcomeInput(
            status="failed",
            action_taken="Restart the worker.",
            observation="The same failure occurred again.",
        ),
    )
    assert receipt.learned is False
    assert store.stats().reusable_memories == 0
