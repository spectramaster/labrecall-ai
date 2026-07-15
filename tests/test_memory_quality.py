from labrecall.agent import RepairAgent
from labrecall.embeddings import HashEmbedder
from labrecall.memory import LocalMemoryStore
from labrecall.models import IncidentInput, OutcomeInput


def _incident(error: str) -> IncidentInput:
    return IncidentInput(
        pipeline="training",
        error=error,
        environment="Python 3.12, GPU 8 GB",
    )


def test_near_duplicate_successes_consolidate_and_calibrate() -> None:
    store = LocalMemoryStore()
    agent = RepairAgent(store, HashEmbedder(64))
    action = "Reduce validation batch size from 64 to 16."

    first = agent.analyze(_incident("CUDA out of memory validation batch 64"))
    first_receipt = agent.learn(
        first.incident_id,
        OutcomeInput(status="worked", action_taken=action, observation="Validation completed."),
    )
    second = agent.analyze(_incident("CUDA out of memory validation batch 64"))
    second_receipt = agent.learn(
        second.incident_id,
        OutcomeInput(status="worked", action_taken=action, observation="Repeat completed."),
    )

    assert second_receipt.promoted_memory_id == first_receipt.promoted_memory_id
    assert store.stats().reusable_memories == 1
    recalled = store.recall(
        HashEmbedder(64).embed(_incident("CUDA out of memory validation batch 64").memory_text()), 1
    )
    assert recalled[0].successful_outcomes == 2
    assert recalled[0].confidence == 0.75


def test_repeated_identical_outcome_is_idempotent() -> None:
    store = LocalMemoryStore()
    agent = RepairAgent(store, HashEmbedder(64))
    recommendation = agent.analyze(_incident("checkpoint write interrupted"))
    outcome = OutcomeInput(
        status="worked",
        action_taken="Write to a temporary key and promote atomically.",
        observation="Three resumed runs completed.",
    )

    first = agent.learn(recommendation.incident_id, outcome)
    second = agent.learn(recommendation.incident_id, outcome)

    assert second.promoted_memory_id == first.promoted_memory_id
    assert store.stats().outcomes == 1
    assert store.stats().reusable_memories == 1
