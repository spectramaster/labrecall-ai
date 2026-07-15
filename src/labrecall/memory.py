import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, TypeVar
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from labrecall.models import IncidentInput, MemoryStats, OutcomeInput, RecalledMemory

T = TypeVar("T")


class MemoryStore(Protocol):
    def create_incident(
        self, incident_id: UUID, incident: IncidentInput, embedding: list[float]
    ) -> None: ...

    def recall(self, embedding: list[float], limit: int) -> list[RecalledMemory]: ...

    def record_outcome(self, incident_id: UUID, outcome: OutcomeInput) -> UUID | None: ...

    def stats(self) -> MemoryStats: ...


@dataclass
class LocalMemoryStore:
    incidents: dict[UUID, tuple[IncidentInput, list[float]]] = field(default_factory=dict)
    outcomes: dict[UUID, OutcomeInput] = field(default_factory=dict)
    memories: dict[UUID, tuple[str, str, list[float], int, int]] = field(default_factory=dict)
    audit_events: list[tuple[datetime, str, UUID]] = field(default_factory=list)

    def create_incident(
        self, incident_id: UUID, incident: IncidentInput, embedding: list[float]
    ) -> None:
        self.incidents[incident_id] = (incident, embedding)
        self.audit_events.append((datetime.now(UTC), "incident.created", incident_id))

    def recall(self, embedding: list[float], limit: int) -> list[RecalledMemory]:
        recalled: list[RecalledMemory] = []
        for memory_id, (signature, action, vector, worked, failed) in self.memories.items():
            similarity = sum(a * b for a, b in zip(embedding, vector, strict=True))
            denom = math.sqrt(sum(a * a for a in embedding) * sum(b * b for b in vector))
            recalled.append(
                RecalledMemory(
                    memory_id=memory_id,
                    similarity=similarity / denom if denom else 0.0,
                    failure_signature=signature,
                    repair_action=action,
                    successful_outcomes=worked,
                    failed_outcomes=failed,
                )
            )
        recalled.sort(
            key=lambda item: (item.similarity, item.successful_outcomes - item.failed_outcomes),
            reverse=True,
        )
        return recalled[:limit]

    def record_outcome(self, incident_id: UUID, outcome: OutcomeInput) -> UUID | None:
        if incident_id not in self.incidents:
            raise KeyError(incident_id)
        self.outcomes[incident_id] = outcome
        self.audit_events.append((datetime.now(UTC), "outcome.recorded", incident_id))
        if outcome.status != "worked":
            return None
        incident, embedding = self.incidents[incident_id]
        memory_id = uuid4()
        self.memories[memory_id] = (incident.error, outcome.action_taken, embedding, 1, 0)
        self.audit_events.append((datetime.now(UTC), "memory.promoted", memory_id))
        return memory_id

    def stats(self) -> MemoryStats:
        return MemoryStats(
            incidents=len(self.incidents),
            outcomes=len(self.outcomes),
            reusable_memories=len(self.memories),
            audit_events=len(self.audit_events),
        )


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.9g}" for value in vector) + "]"


class CockroachMemoryStore:
    """Transactional memory store with namespace-prefixed vector recall."""

    def __init__(self, database_url: str, namespace: str, max_retries: int = 3) -> None:
        self.database_url = database_url
        self.namespace = namespace
        self.max_retries = max_retries

    def _transaction(self, operation: Callable[[psycopg.Connection], T]) -> T:
        for attempt in range(self.max_retries):
            try:
                with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
                    result = operation(connection)
                    connection.commit()
                    return result
            except psycopg.errors.SerializationFailure:
                if attempt + 1 == self.max_retries:
                    raise
                time.sleep(0.05 * (2**attempt))
        raise RuntimeError("transaction retry loop exhausted")

    def create_incident(
        self, incident_id: UUID, incident: IncidentInput, embedding: list[float]
    ) -> None:
        def operation(connection: psycopg.Connection) -> None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO incidents (
                        id, namespace, pipeline, error, environment,
                        attempted_actions, constraints, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::VECTOR)
                    """,
                    (
                        incident_id,
                        self.namespace,
                        incident.pipeline,
                        incident.error,
                        incident.environment,
                        Jsonb(incident.attempted_actions),
                        Jsonb(incident.constraints),
                        _vector_literal(embedding),
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO audit_events
                        (id, namespace, event_type, subject_id, detail)
                    VALUES (%s, %s, 'incident.created', %s, %s)
                    """,
                    (uuid4(), self.namespace, incident_id, Jsonb({"pipeline": incident.pipeline})),
                )

        self._transaction(operation)

    def recall(self, embedding: list[float], limit: int) -> list[RecalledMemory]:
        vector = _vector_literal(embedding)

        def operation(connection: psycopg.Connection) -> list[RecalledMemory]:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, 1 - (embedding <=> %s::VECTOR) AS similarity,
                           failure_signature, repair_action,
                           successful_outcomes, failed_outcomes
                    FROM repair_memories
                    WHERE namespace = %s
                    ORDER BY embedding <=> %s::VECTOR
                    LIMIT %s
                    """,
                    (vector, self.namespace, vector, limit),
                )
                rows = cursor.fetchall()
                return [
                    RecalledMemory(
                        memory_id=row["id"],
                        similarity=float(row["similarity"]),
                        failure_signature=row["failure_signature"],
                        repair_action=row["repair_action"],
                        successful_outcomes=row["successful_outcomes"],
                        failed_outcomes=row["failed_outcomes"],
                    )
                    for row in rows
                ]

        recalled = self._transaction(operation)
        return recalled

    def record_outcome(self, incident_id: UUID, outcome: OutcomeInput) -> UUID | None:
        def operation(connection: psycopg.Connection) -> UUID | None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT error, embedding
                    FROM incidents
                    WHERE id = %s AND namespace = %s
                    FOR UPDATE
                    """,
                    (incident_id, self.namespace),
                )
                incident = cursor.fetchone()
                if incident is None:
                    raise KeyError(incident_id)
                cursor.execute(
                    """
                    INSERT INTO outcomes
                        (incident_id, status, action_taken, observation, side_effects)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        incident_id,
                        outcome.status,
                        outcome.action_taken,
                        outcome.observation,
                        Jsonb(outcome.side_effects),
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO audit_events
                        (id, namespace, event_type, subject_id, detail)
                    VALUES (%s, %s, 'outcome.recorded', %s, %s)
                    """,
                    (uuid4(), self.namespace, incident_id, Jsonb({"status": outcome.status})),
                )
                if outcome.status != "worked":
                    return None

                memory_id = uuid4()
                cursor.execute(
                    """
                    INSERT INTO repair_memories (
                        id, source_incident_id, namespace, failure_signature,
                        repair_action, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        memory_id,
                        incident_id,
                        self.namespace,
                        incident["error"],
                        outcome.action_taken,
                        incident["embedding"],
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO audit_events
                        (id, namespace, event_type, subject_id, evidence_ids, detail)
                    VALUES (%s, %s, 'memory.promoted', %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        self.namespace,
                        memory_id,
                        [incident_id],
                        Jsonb({"outcome_status": outcome.status}),
                    ),
                )
                return memory_id

        return self._transaction(operation)

    def stats(self) -> MemoryStats:
        def operation(connection: psycopg.Connection) -> MemoryStats:
            with connection.cursor() as cursor:
                counts: dict[str, int] = {}
                for table in ("incidents", "outcomes", "repair_memories", "audit_events"):
                    namespace_clause = "namespace = %s"
                    if table == "outcomes":
                        namespace_clause = (
                            "incident_id IN (SELECT id FROM incidents WHERE namespace = %s)"
                        )
                    cursor.execute(
                        f"SELECT count(*) AS count FROM {table} WHERE {namespace_clause}",
                        (self.namespace,),
                    )
                    counts[table] = int(cursor.fetchone()["count"])
                return MemoryStats(
                    incidents=counts["incidents"],
                    outcomes=counts["outcomes"],
                    reusable_memories=counts["repair_memories"],
                    audit_events=counts["audit_events"],
                )

        return self._transaction(operation)
