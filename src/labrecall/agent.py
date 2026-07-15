from uuid import UUID, uuid4

from labrecall.embeddings import Embedder
from labrecall.generation import Explainer
from labrecall.memory import MemoryStore
from labrecall.models import IncidentInput, OutcomeInput, OutcomeReceipt, Recommendation


class RepairAgent:
    def __init__(
        self,
        store: MemoryStore,
        embedder: Embedder,
        mode: str = "fixture",
        retrieval_limit: int = 5,
        explainer: Explainer | None = None,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.mode = mode
        self.retrieval_limit = retrieval_limit
        self.explainer = explainer

    def analyze(self, incident: IncidentInput) -> Recommendation:
        incident_id = uuid4()
        embedding = self.embedder.embed(incident.memory_text())
        self.store.create_incident(incident_id, incident, embedding)
        evidence = self.store.recall(embedding, self.retrieval_limit)

        if evidence:
            strongest = evidence[0]
            actions = [
                "Reproduce the failure with a read-only diagnostic and preserve the logs.",
                strongest.repair_action,
                "Run the narrowest relevant validation before accepting the repair.",
            ]
            summary = (
                "A prior confirmed repair is semantically similar; verify its assumptions "
                "before reuse. "
                f"Memory similarity: {strongest.similarity:.3f}; "
                f"outcome confidence: {strongest.confidence:.3f}."
            )
        else:
            actions = [
                "Capture the minimal reproducible failure and environment fingerprint.",
                "Run read-only diagnostics that test one hypothesis at a time.",
                "Record the observed outcome before promoting any repair to memory.",
            ]
            summary = "No confirmed repair memory was found; use a bounded diagnostic plan."

        if self.explainer:
            summary = self.explainer.explain(incident, evidence, actions)

        return Recommendation(
            incident_id=incident_id,
            summary=summary,
            proposed_actions=actions,
            evidence=evidence,
            mode=self.mode,
        )

    def learn(self, incident_id: UUID, outcome: OutcomeInput) -> OutcomeReceipt:
        memory_id = self.store.record_outcome(incident_id, outcome)
        if memory_id is None:
            return OutcomeReceipt(
                incident_id=incident_id,
                learned=False,
                reason="Only human-confirmed successful outcomes become reusable memory.",
            )
        return OutcomeReceipt(
            incident_id=incident_id,
            promoted_memory_id=memory_id,
            learned=True,
            reason="The confirmed repair was promoted with its original failure embedding.",
        )
