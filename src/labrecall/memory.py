import math
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, TypeVar
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from labrecall.models import AuditEvent, IncidentInput, MemoryStats, OutcomeInput, RecalledMemory

T = TypeVar("T")
CONSOLIDATION_THRESHOLD = 0.92


class AmbiguousCommitError(RuntimeError):
    """Raised when a non-idempotent transaction has an unknown commit outcome."""


class MemoryStore(Protocol):
    def create_incident(
        self, incident_id: UUID, incident: IncidentInput, embedding: list[float]
    ) -> None: ...

    def recall(self, embedding: list[float], limit: int) -> list[RecalledMemory]: ...

    def record_outcome(self, incident_id: UUID, outcome: OutcomeInput) -> UUID | None: ...

    def record_recommendation(
        self,
        incident_id: UUID,
        evidence_ids: list[UUID],
        detail: dict[str, object],
    ) -> None: ...

    def stats(self) -> MemoryStats: ...

    def recent_audit_events(self, limit: int) -> list[AuditEvent]: ...


@dataclass
class LocalMemoryStore:
    incidents: dict[UUID, tuple[IncidentInput, list[float]]] = field(default_factory=dict)
    outcomes: dict[UUID, OutcomeInput] = field(default_factory=dict)
    memories: dict[UUID, tuple[str, str, list[float], int, int]] = field(default_factory=dict)
    promoted: dict[UUID, UUID] = field(default_factory=dict)
    audit_events: list[AuditEvent] = field(default_factory=list)

    def _audit(
        self,
        event_type: str,
        subject_id: UUID,
        *,
        evidence_ids: list[UUID] | None = None,
        detail: dict[str, object] | None = None,
    ) -> None:
        self.audit_events.append(
            AuditEvent(
                created_at=datetime.now(UTC),
                event_type=event_type,
                subject_id=subject_id,
                evidence_ids=evidence_ids or [],
                detail=detail or {},
            )
        )

    def create_incident(
        self, incident_id: UUID, incident: IncidentInput, embedding: list[float]
    ) -> None:
        if incident_id not in self.incidents:
            self.incidents[incident_id] = (incident, embedding)
            self._audit("incident.created", incident_id, detail={"pipeline": incident.pipeline})

    @staticmethod
    def _similarity(left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        denom = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
        return dot / denom if denom else 0.0

    def recall(self, embedding: list[float], limit: int) -> list[RecalledMemory]:
        recalled: list[RecalledMemory] = []
        for memory_id, (signature, action, vector, worked, failed) in self.memories.items():
            similarity = self._similarity(embedding, vector)
            recalled.append(
                RecalledMemory(
                    memory_id=memory_id,
                    similarity=similarity,
                    failure_signature=signature,
                    repair_action=action,
                    successful_outcomes=worked,
                    failed_outcomes=failed,
                    confidence=(worked + 1) / (worked + failed + 2),
                    ranking_score=similarity * ((worked + 1) / (worked + failed + 2)),
                )
            )
        recalled.sort(
            key=lambda item: (item.similarity * item.confidence, item.confidence),
            reverse=True,
        )
        return recalled[:limit]

    def record_outcome(self, incident_id: UUID, outcome: OutcomeInput) -> UUID | None:
        if incident_id not in self.incidents:
            raise KeyError(incident_id)
        if incident_id in self.outcomes:
            if self.outcomes[incident_id] != outcome:
                raise ValueError("outcome already recorded with different evidence")
            return self.promoted.get(incident_id)
        self.outcomes[incident_id] = outcome
        self._audit("outcome.recorded", incident_id, detail={"status": outcome.status})
        incident, embedding = self.incidents[incident_id]

        nearest: tuple[UUID, float] | None = None
        for memory_id, (_, action, vector, _, _) in self.memories.items():
            if action != outcome.action_taken:
                continue
            similarity = self._similarity(embedding, vector)
            if nearest is None or similarity > nearest[1]:
                nearest = (memory_id, similarity)

        if outcome.status == "failed":
            if nearest and nearest[1] >= CONSOLIDATION_THRESHOLD:
                memory_id = nearest[0]
                signature, action, vector, worked, failed = self.memories[memory_id]
                self.memories[memory_id] = (signature, action, vector, worked, failed + 1)
                self._audit(
                    "memory.confidence_updated",
                    memory_id,
                    evidence_ids=[incident_id],
                    detail={"outcome_status": "failed"},
                )
            return None
        if outcome.status != "worked":
            return None

        if nearest and nearest[1] >= CONSOLIDATION_THRESHOLD:
            memory_id = nearest[0]
            signature, action, vector, worked, failed = self.memories[memory_id]
            self.memories[memory_id] = (signature, action, vector, worked + 1, failed)
            self.promoted[incident_id] = memory_id
            self._audit(
                "memory.consolidated",
                memory_id,
                evidence_ids=[incident_id],
                detail={"outcome_status": "worked"},
            )
            return memory_id

        memory_id = uuid4()
        self.memories[memory_id] = (incident.error, outcome.action_taken, embedding, 1, 0)
        self.promoted[incident_id] = memory_id
        self._audit(
            "memory.promoted",
            memory_id,
            evidence_ids=[incident_id],
            detail={"outcome_status": "worked"},
        )
        return memory_id

    def record_recommendation(
        self,
        incident_id: UUID,
        evidence_ids: list[UUID],
        detail: dict[str, object],
    ) -> None:
        self._audit(
            "memory.retrieved",
            incident_id,
            evidence_ids=evidence_ids,
            detail={"retrieved_count": len(evidence_ids)},
        )
        self._audit(
            "recommendation.created",
            incident_id,
            evidence_ids=evidence_ids,
            detail=detail,
        )

    def stats(self) -> MemoryStats:
        return MemoryStats(
            incidents=len(self.incidents),
            outcomes=len(self.outcomes),
            reusable_memories=len(self.memories),
            audit_events=len(self.audit_events),
        )

    def recent_audit_events(self, limit: int) -> list[AuditEvent]:
        return list(reversed(self.audit_events[-limit:]))


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.9g}" for value in vector) + "]"


class CockroachMemoryStore:
    """Transactional memory store with namespace-prefixed vector recall."""

    def __init__(self, database_url: str, namespace: str, max_retries: int = 3) -> None:
        self.database_url = database_url
        self.namespace = namespace
        self.max_retries = max_retries

    def _transaction(
        self,
        operation: Callable[[psycopg.Connection], T],
        *,
        idempotent: bool = False,
    ) -> T:
        for attempt in range(self.max_retries):
            try:
                with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
                    result = operation(connection)
                    connection.commit()
                    return result
            except psycopg.errors.SerializationFailure:
                if attempt + 1 == self.max_retries:
                    raise
                base = 0.05 * (2**attempt)
                time.sleep(base + (secrets.randbelow(1001) / 1000) * base)
            except psycopg.errors.StatementCompletionUnknown as error:
                if not idempotent or attempt + 1 == self.max_retries:
                    raise AmbiguousCommitError(
                        "transaction commit outcome is unknown; inspect by operation ID"
                    ) from error
                base = 0.05 * (2**attempt)
                time.sleep(base + (secrets.randbelow(1001) / 1000) * base)
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
                    ON CONFLICT (id) DO NOTHING
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
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        uuid5(NAMESPACE_URL, f"incident:{self.namespace}:{incident_id}"),
                        self.namespace,
                        incident_id,
                        Jsonb({"pipeline": incident.pipeline}),
                    ),
                )

        self._transaction(operation, idempotent=True)

    def recall(self, embedding: list[float], limit: int) -> list[RecalledMemory]:
        vector = _vector_literal(embedding)

        def operation(connection: psycopg.Connection) -> list[RecalledMemory]:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, 1 - (embedding <=> %s::VECTOR) AS similarity,
                           failure_signature, repair_action,
                           successful_outcomes, failed_outcomes
                           , (successful_outcomes + 1.0) /
                             (successful_outcomes + failed_outcomes + 2.0) AS confidence
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
                        confidence=float(row["confidence"]),
                        ranking_score=(
                            float(row["similarity"])
                            * float(row["confidence"])
                        ),
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
                    ON CONFLICT (incident_id) DO NOTHING
                    """,
                    (
                        incident_id,
                        outcome.status,
                        outcome.action_taken,
                        outcome.observation,
                        Jsonb(outcome.side_effects),
                    ),
                )
                outcome_inserted = cursor.rowcount == 1
                cursor.execute(
                    """
                    SELECT status, action_taken, observation, side_effects
                    FROM outcomes WHERE incident_id = %s
                    """,
                    (incident_id,),
                )
                recorded = cursor.fetchone()
                if (
                    recorded["status"] != outcome.status
                    or recorded["action_taken"] != outcome.action_taken
                    or recorded["observation"] != outcome.observation
                ):
                    raise ValueError("outcome already recorded with different evidence")
                if not outcome_inserted:
                    cursor.execute(
                        """
                        SELECT id FROM repair_memories
                        WHERE source_incident_id = %s AND namespace = %s
                        """,
                        (incident_id, self.namespace),
                    )
                    existing_memory = cursor.fetchone()
                    return existing_memory["id"] if existing_memory else None
                cursor.execute(
                    """
                    INSERT INTO audit_events
                        (id, namespace, event_type, subject_id, detail)
                    VALUES (%s, %s, 'outcome.recorded', %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        uuid5(NAMESPACE_URL, f"outcome:{self.namespace}:{incident_id}"),
                        self.namespace,
                        incident_id,
                        Jsonb({"status": outcome.status}),
                    ),
                )

                vector = str(incident["embedding"])
                cursor.execute(
                    """
                    SELECT id, 1 - (embedding <=> %s::VECTOR) AS similarity
                    FROM repair_memories
                    WHERE namespace = %s AND repair_action = %s
                    ORDER BY embedding <=> %s::VECTOR
                    LIMIT 1
                    """,
                    (vector, self.namespace, outcome.action_taken, vector),
                )
                nearest = cursor.fetchone()

                if outcome.status == "failed":
                    if nearest and float(nearest["similarity"]) >= CONSOLIDATION_THRESHOLD:
                        memory_id = nearest["id"]
                        cursor.execute(
                            """
                            UPDATE repair_memories
                            SET failed_outcomes = failed_outcomes + 1
                            WHERE id = %s
                            """,
                            (memory_id,),
                        )
                        cursor.execute(
                            """
                            INSERT INTO audit_events
                                (id, namespace, event_type, subject_id, evidence_ids, detail)
                            VALUES (%s, %s, 'memory.confidence_updated', %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                            """,
                            (
                                uuid5(
                                    NAMESPACE_URL,
                                    f"failed-reuse:{self.namespace}:{incident_id}",
                                ),
                                self.namespace,
                                memory_id,
                                [incident_id],
                                Jsonb({"outcome_status": "failed"}),
                            ),
                        )
                    return None
                if outcome.status != "worked":
                    return None

                if nearest and float(nearest["similarity"]) >= CONSOLIDATION_THRESHOLD:
                    memory_id = nearest["id"]
                    cursor.execute(
                        """
                        UPDATE repair_memories
                        SET successful_outcomes = successful_outcomes + 1
                        WHERE id = %s
                        """,
                        (memory_id,),
                    )
                    cursor.execute(
                        """
                        INSERT INTO audit_events
                            (id, namespace, event_type, subject_id, evidence_ids, detail)
                        VALUES (%s, %s, 'memory.consolidated', %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            uuid5(NAMESPACE_URL, f"consolidated:{self.namespace}:{incident_id}"),
                            self.namespace,
                            memory_id,
                            [incident_id],
                            Jsonb({"outcome_status": "worked"}),
                        ),
                    )
                    return memory_id

                memory_id = uuid5(NAMESPACE_URL, f"memory:{self.namespace}:{incident_id}")
                cursor.execute(
                    """
                    INSERT INTO repair_memories (
                        id, source_incident_id, namespace, failure_signature,
                        repair_action, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_incident_id) DO NOTHING
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
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        uuid5(NAMESPACE_URL, f"promotion:{self.namespace}:{incident_id}"),
                        self.namespace,
                        memory_id,
                        [incident_id],
                        Jsonb({"outcome_status": outcome.status}),
                    ),
                )
                return memory_id

        return self._transaction(operation)

    def recent_audit_events(self, limit: int) -> list[AuditEvent]:
        def operation(connection: psycopg.Connection) -> list[AuditEvent]:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT created_at, event_type, subject_id, evidence_ids, detail
                    FROM audit_events
                    WHERE namespace = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (self.namespace, limit),
                )
                return [
                    AuditEvent(
                        created_at=row["created_at"],
                        event_type=row["event_type"],
                        subject_id=row["subject_id"],
                        evidence_ids=list(row["evidence_ids"] or []),
                        detail=dict(row["detail"] or {}),
                    )
                    for row in cursor.fetchall()
                ]

        return self._transaction(operation)

    def record_recommendation(
        self,
        incident_id: UUID,
        evidence_ids: list[UUID],
        detail: dict[str, object],
    ) -> None:
        def operation(connection: psycopg.Connection) -> None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_events
                        (id, namespace, event_type, subject_id, evidence_ids, detail)
                    VALUES
                        (%s, %s, 'memory.retrieved', %s, %s, %s),
                        (%s, %s, 'recommendation.created', %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        uuid5(NAMESPACE_URL, f"retrieval:{self.namespace}:{incident_id}"),
                        self.namespace,
                        incident_id,
                        evidence_ids,
                        Jsonb({"retrieved_count": len(evidence_ids)}),
                        uuid5(NAMESPACE_URL, f"recommendation:{self.namespace}:{incident_id}"),
                        self.namespace,
                        incident_id,
                        evidence_ids,
                        Jsonb(detail),
                    ),
                )

        self._transaction(operation, idempotent=True)

    def stats(self) -> MemoryStats:
        def operation(connection: psycopg.Connection) -> MemoryStats:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        (SELECT count(*) FROM incidents WHERE namespace = %s) AS incidents,
                        (
                            SELECT count(*)
                            FROM outcomes
                            WHERE incident_id IN (
                                SELECT id FROM incidents WHERE namespace = %s
                            )
                        ) AS outcomes,
                        (
                            SELECT count(*)
                            FROM repair_memories
                            WHERE namespace = %s
                        ) AS repair_memories,
                        (
                            SELECT count(*)
                            FROM audit_events
                            WHERE namespace = %s
                        ) AS audit_events
                    """,
                    (self.namespace, self.namespace, self.namespace, self.namespace),
                )
                counts = cursor.fetchone()
                return MemoryStats(
                    incidents=counts["incidents"],
                    outcomes=counts["outcomes"],
                    reusable_memories=counts["repair_memories"],
                    audit_events=counts["audit_events"],
                )

        return self._transaction(operation)
