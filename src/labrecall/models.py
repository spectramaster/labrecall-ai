from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IncidentInput(BaseModel):
    pipeline: str = Field(min_length=2, max_length=120)
    error: str = Field(min_length=3, max_length=4000)
    environment: str = Field(min_length=2, max_length=1000)
    attempted_actions: list[str] = Field(default_factory=list, max_length=12)
    constraints: list[str] = Field(default_factory=list, max_length=12)

    def memory_text(self) -> str:
        actions = "; ".join(self.attempted_actions) or "none"
        constraints = "; ".join(self.constraints) or "none"
        return (
            f"pipeline={self.pipeline}\nerror={self.error}\nenvironment={self.environment}\n"
            f"attempted={actions}\nconstraints={constraints}"
        )


class RecalledMemory(BaseModel):
    memory_id: UUID
    similarity: float
    failure_signature: str
    repair_action: str
    successful_outcomes: int
    failed_outcomes: int
    confidence: float = Field(ge=0.0, le=1.0)


class Recommendation(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str
    proposed_actions: list[str]
    evidence: list[RecalledMemory]
    requires_human_approval: bool = True
    mode: Literal["fixture", "cloud"]


class OutcomeInput(BaseModel):
    status: Literal["worked", "failed", "partial"]
    action_taken: str = Field(min_length=3, max_length=2000)
    observation: str = Field(min_length=3, max_length=4000)
    side_effects: list[str] = Field(default_factory=list, max_length=12)


class OutcomeReceipt(BaseModel):
    incident_id: UUID
    promoted_memory_id: UUID | None = None
    learned: bool
    reason: str


class MemoryStats(BaseModel):
    incidents: int
    outcomes: int
    reusable_memories: int
    audit_events: int
