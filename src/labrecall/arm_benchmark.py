import argparse
import json
import math
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class EndpointResult:
    label: str
    architecture: str
    samples: int
    successes: int
    mean_ms: float
    p50_ms: float
    p95_ms: float


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("at least one value is required")
    ordered = sorted(values)
    rank = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[rank]


def _json_request(url: str, payload: dict[str, object] | None, timeout: float) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"content-type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 -- operator URL
        return json.loads(response.read())


def measure_endpoint(
    base_url: str,
    label: str,
    samples: int,
    warmups: int,
    timeout: float,
) -> EndpointResult:
    base_url = base_url.rstrip("/")
    health = _json_request(f"{base_url}/health", None, timeout)
    architecture = str(health.get("architecture", "unknown"))
    durations: list[float] = []
    successes = 0
    total = warmups + samples
    for index in range(total):
        payload = {
            "pipeline": "synthetic Arm architecture benchmark",
            "error": f"repeatable benchmark incident {index}: simulated calibration drift",
            "environment": f"{label} Lambda; synthetic data only",
            "attempted_actions": [],
            "constraints": ["benchmark only", "do not execute proposed actions"],
        }
        started = time.perf_counter()
        try:
            result = _json_request(f"{base_url}/api/incidents", payload, timeout)
            succeeded = bool(result.get("incident_id"))
        except Exception:
            succeeded = False
        elapsed_ms = (time.perf_counter() - started) * 1000
        if index >= warmups:
            durations.append(elapsed_ms)
            successes += int(succeeded)

    return EndpointResult(
        label=label,
        architecture=architecture,
        samples=samples,
        successes=successes,
        mean_ms=round(statistics.mean(durations), 3),
        p50_ms=round(percentile(durations, 0.50), 3),
        p95_ms=round(percentile(durations, 0.95), 3),
    )


def compare(arm: EndpointResult, x86: EndpointResult) -> dict[str, object]:
    latency_change = (arm.mean_ms / x86.mean_ms - 1) * 100 if x86.mean_ms else 0.0
    return {
        "method": "sequential end-to-end HTTPS; excludes warmups",
        "warning": (
            "Client latency is not Lambda billed duration. Use CloudWatch REPORT data, "
            "AWS Lambda Power Tuning, and Arm Performix before making a cost claim."
        ),
        "arm": asdict(arm),
        "x86": asdict(x86),
        "arm_mean_latency_change_percent": round(latency_change, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare LabRecall on Arm64 and x86 Lambda")
    parser.add_argument("--arm-url", required=True)
    parser.add_argument("--x86-url", required=True)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=40.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.samples < 3 or args.warmups < 0:
        parser.error("samples must be at least 3 and warmups cannot be negative")

    arm = measure_endpoint(args.arm_url, "arm64", args.samples, args.warmups, args.timeout)
    x86 = measure_endpoint(args.x86_url, "x86_64", args.samples, args.warmups, args.timeout)
    report = compare(arm, x86)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
