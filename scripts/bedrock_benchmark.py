import argparse
import json
from datetime import UTC, datetime

import boto3

from labrecall.benchmark import run_benchmark
from labrecall.embeddings import BedrockTitanEmbedder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LabRecall's frozen memory benchmark with Bedrock Titan embeddings."
    )
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--model", default="amazon.titan-embed-text-v2:0")
    parser.add_argument("--dimensions", type=int, default=1024)
    parser.add_argument("--selection-threshold", type=float, default=0.65)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = boto3.client("bedrock-runtime", region_name=args.region)
    embedder = BedrockTitanEmbedder(client, args.model, args.dimensions)
    result = run_benchmark(
        embedder,
        embedding_label=f"{args.model} ({args.dimensions} dimensions)",
        selection_threshold=args.selection_threshold,
    )
    result["cloud_run"] = {
        "captured_at": datetime.now(UTC).isoformat(),
        "region": args.region,
        "model": args.model,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
