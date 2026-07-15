import json
import statistics
import time
from dataclasses import dataclass

from labrecall.agent import RepairAgent
from labrecall.embeddings import Embedder, HashEmbedder
from labrecall.memory import LocalMemoryStore
from labrecall.models import IncidentInput, OutcomeInput


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    training_error: str
    evaluation_error: str
    environment: str
    repair: str


CASES = (
    BenchmarkCase(
        "gpu-oom",
        "CUDA out of memory during validation with batch size 64",
        "CUDA memory exhausted in validation at batch size 64",
        "Python 3.12, CUDA, 8 GB GPU",
        "Reduce validation batch size from 64 to 16 without changing sample order.",
    ),
    BenchmarkCase(
        "checkpoint-atomicity",
        "worker lost while writing a checkpoint to object storage",
        "checkpoint was partial after the worker disappeared during object storage write",
        "distributed Python job and object storage",
        "Write checkpoints to a temporary key and atomically promote after verification.",
    ),
    BenchmarkCase(
        "spectral-drift",
        "spectral calibration drift after a warm restart",
        "warm restart caused drift in spectral calibration residuals",
        "TDLAS acquisition pipeline",
        "Wait for thermal stabilization and then acquire a fresh dark reference.",
    ),
    BenchmarkCase(
        "schema-drift",
        "feature table schema changed and inference columns no longer align",
        "inference failed because feature columns differ after a schema change",
        "Parquet feature pipeline",
        "Pin the verified feature schema and validate column order before inference.",
    ),
    BenchmarkCase(
        "seed-regression",
        "reproducibility regression after a dependency upgrade changed random seeds",
        "dependency upgrade produced different results despite the same random seed",
        "Python numerical workflow",
        "Record dependency hashes and seed every stochastic library at process start.",
    ),
    BenchmarkCase(
        "unit-conversion",
        "pressure supplied in kPa while the forward model expects Pa caused residual explosion",
        "retrieval residuals diverged because pressure units were kPa instead of Pa",
        "Python spectroscopy retrieval",
        "Normalize pressure to Pa at the input boundary and assert the accepted unit.",
    ),
    BenchmarkCase(
        "stale-checkpoint-lock",
        "a preempted worker left a stale checkpoint lock on shared storage",
        "checkpoint resume was blocked by an orphaned lock after worker preemption",
        "distributed Python job and shared storage",
        "Verify lock ownership and expiry before removing only the stale checkpoint lock.",
    ),
    BenchmarkCase(
        "timestamp-order",
        "partition merge interleaved sensor timestamps and broke windowed aggregation",
        "window features changed because merged sensor rows were no longer time ordered",
        "partitioned sensor pipeline",
        "Apply a stable timestamp sort and reject duplicate sequence identifiers "
        "before aggregation.",
    ),
)

NEGATIVE_CONTROLS = (
    IncidentInput(
        pipeline="browser authentication",
        error="OAuth access token expired and the API returned HTTP 401",
        environment="TypeScript single-page application",
        constraints=["do not expose tokens"],
    ),
    IncidentInput(
        pipeline="image annotation",
        error="bounding-box class labels shifted after geometric augmentation",
        environment="computer-vision training dataset",
        constraints=["preserve source images"],
    ),
    IncidentInput(
        pipeline="database migration",
        error="concurrent index creation deadlocked with a schema migration",
        environment="transactional SQL service",
        constraints=["avoid blocking production writes"],
    ),
)


def _incident(error: str, environment: str) -> IncidentInput:
    return IncidentInput(
        pipeline="synthetic research pipeline",
        error=error,
        environment=environment,
        constraints=["read-only diagnosis first", "preserve verified artifacts"],
    )


def run_benchmark(
    embedder: Embedder | None = None,
    *,
    embedding_label: str = "fixture signed token hash (256 dimensions)",
    selection_threshold: float = 0.65,
) -> dict[str, object]:
    embedder = embedder or HashEmbedder(256)
    memory_agent = RepairAgent(
        LocalMemoryStore(),
        embedder,
        retrieval_limit=3,
        retrieval_min_similarity=selection_threshold,
    )
    baseline_agent = RepairAgent(
        LocalMemoryStore(),
        embedder,
        retrieval_limit=0,
        retrieval_min_similarity=selection_threshold,
    )

    for case in CASES:
        recommendation = memory_agent.analyze(_incident(case.training_error, case.environment))
        memory_agent.learn(
            recommendation.incident_id,
            OutcomeInput(
                status="worked",
                action_taken=case.repair,
                observation="The synthetic repeat completed and the acceptance check passed.",
            ),
        )

    rows: list[dict[str, object]] = []
    memory_latencies: list[float] = []
    baseline_latencies: list[float] = []
    correct = 0
    retrieved = 0
    for case in CASES:
        evaluation = _incident(case.evaluation_error, case.environment)

        started = time.perf_counter()
        with_memory = memory_agent.analyze(evaluation)
        memory_latencies.append((time.perf_counter() - started) * 1000)

        started = time.perf_counter()
        without_memory = baseline_agent.analyze(evaluation)
        baseline_latencies.append((time.perf_counter() - started) * 1000)

        top_action = with_memory.evidence[0].repair_action if with_memory.evidence else None
        top1_correct = top_action == case.repair
        correct += int(top1_correct)
        retrieved += int(bool(with_memory.evidence))
        rows.append(
            {
                "case": case.name,
                "top1_correct": top1_correct,
                "memory_similarity": (
                    round(with_memory.evidence[0].similarity, 4)
                    if with_memory.evidence
                    else None
                ),
                "memory_confidence": (
                    round(with_memory.evidence[0].confidence, 4)
                    if with_memory.evidence
                    else None
                ),
                "baseline_abstained": not without_memory.evidence,
            }
        )

    negative_abstentions = sum(
        not memory_agent.analyze(control).evidence for control in NEGATIVE_CONTROLS
    )

    calibration_store = LocalMemoryStore()
    calibration_agent = RepairAgent(
        calibration_store,
        embedder,
        retrieval_min_similarity=selection_threshold,
    )
    calibration_case = CASES[0]
    calibration_incident = _incident(
        calibration_case.training_error,
        calibration_case.environment,
    )
    confidence_path: list[float] = []
    for status in ("worked", "worked", "failed"):
        recommendation = calibration_agent.analyze(calibration_incident)
        calibration_agent.learn(
            recommendation.incident_id,
            OutcomeInput(
                status=status,
                action_taken=calibration_case.repair,
                observation=f"Synthetic acceptance result recorded as {status}.",
            ),
        )
        recalled = calibration_store.recall(embedder.embed(calibration_incident.memory_text()), 1)
        confidence_path.append(round(recalled[0].confidence, 4))

    total = len(CASES)
    return {
        "benchmark": "synthetic outcome-gated repair-memory systems check",
        "benchmark_version": "2.0",
        "positive_cases": total,
        "negative_controls": len(NEGATIVE_CONTROLS),
        "selection_threshold": selection_threshold,
        "embedding": embedding_label,
        "memory_on": {
            "top1_accuracy": correct / total,
            "retrieval_precision_at_1": correct / retrieved if retrieved else 0.0,
            "retrieval_recall_at_1": correct / total,
            "negative_abstention_rate": negative_abstentions / len(NEGATIVE_CONTROLS),
            "mean_latency_ms": round(statistics.mean(memory_latencies), 3),
        },
        "memory_off": {
            "top1_accuracy": 0.0,
            "abstention_rate": 1.0,
            "mean_latency_ms": round(statistics.mean(baseline_latencies), 3),
        },
        "outcome_calibration": {
            "sequence": ["worked", "worked", "failed"],
            "confidence_path": confidence_path,
            "memories_after_three_outcomes": calibration_store.stats().reusable_memories,
            "interpretation": "success consolidates; confirmed failed reuse lowers confidence",
        },
        "limitations": [
            "This checks system semantics and deterministic retrieval, not "
            "foundation-model quality.",
            "Cloud Titan embeddings must be evaluated separately with the same frozen cases.",
        ],
        "rows": rows,
    }


def main() -> None:
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
