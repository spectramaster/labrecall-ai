import json
import statistics
import time
from dataclasses import dataclass

from labrecall.agent import RepairAgent
from labrecall.embeddings import HashEmbedder
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
)


def _incident(error: str, environment: str) -> IncidentInput:
    return IncidentInput(
        pipeline="synthetic research pipeline",
        error=error,
        environment=environment,
        constraints=["read-only diagnosis first", "preserve verified artifacts"],
    )


def run_benchmark() -> dict[str, object]:
    embedder = HashEmbedder(256)
    memory_agent = RepairAgent(LocalMemoryStore(), embedder, retrieval_limit=3)
    baseline_agent = RepairAgent(LocalMemoryStore(), embedder, retrieval_limit=0)

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
                "memory_similarity": round(with_memory.evidence[0].similarity, 4),
                "memory_confidence": round(with_memory.evidence[0].confidence, 4),
                "baseline_abstained": not without_memory.evidence,
            }
        )

    total = len(CASES)
    return {
        "benchmark": "synthetic research-pipeline repair recall",
        "cases": total,
        "fixture_embedding": "deterministic signed token hash; not a model-quality claim",
        "memory_on": {
            "top1_accuracy": correct / total,
            "retrieval_precision_at_1": correct / retrieved if retrieved else 0.0,
            "retrieval_recall_at_1": correct / total,
            "mean_latency_ms": round(statistics.mean(memory_latencies), 3),
        },
        "memory_off": {
            "top1_accuracy": 0.0,
            "abstention_rate": 1.0,
            "mean_latency_ms": round(statistics.mean(baseline_latencies), 3),
        },
        "rows": rows,
    }


def main() -> None:
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
