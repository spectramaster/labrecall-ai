# Arm64 optimization and evidence plan

## Competition fit

LabRecall is a reference agentic-memory service for the Cloud AI track. The Arm entry is
not based on changing one template field: it turns the service into a reproducible
Arm64 migration and validation workflow for Python AI agents that combine native wheels,
serverless orchestration, model calls, and a remote vector database.

The repository already uses an MIT license and builds an Arm64 Lambda package. The
competition contribution adds dual-architecture deployment, isolated benchmark data,
runtime architecture proof, bounded load generation, and an evidence pipeline.

## Measurement contract

Two stacks must be deployed from the same commit and configuration except for:

| Stack | Lambda architecture | CockroachDB namespace |
|---|---|---|
| LabRecall Arm | `arm64` | `benchmark-arm64` |
| LabRecall control | `x86_64` | `benchmark-x86` |

Run at least three repetitions of each experiment and publish raw JSON alongside the
summary. Report median and p95, not only the best run. Do not call client-observed HTTPS
latency a billed-duration or energy measurement.

## Evidence ladder

1. **Compatibility:** build each architecture in its matching Linux container and prove
   the `psycopg` native wheel imports on Lambda.
2. **Correctness:** run the same API and memory lifecycle tests on both stacks.
3. **End-to-end latency:** run `labrecall.arm_benchmark` against both public endpoints.
4. **Lambda cost/performance:** use the open-source AWS Lambda Power Tuning workflow and
   export its raw state-machine results.
5. **Hardware analysis:** profile the representative Python workload on an Arm Neoverse
   system with Arm Performix and preserve machine-readable output and screenshots.
6. **Operational value:** document build time, package size, cold/warm behavior, failure
   rate, and the exact migration changes so other Agent developers can reproduce them.

## Commands after AWS authentication

Build and deploy separate stacks with architecture-matched container builds. Substitute
the real secret ARN only in the local shell or deployment environment.

```bash
sam build --template-file infra/aws/template.yaml --use-container \
  --parameter-overrides Architecture=arm64 MemoryNamespace=benchmark-arm64
sam deploy --stack-name labrecall-arm64 --resolve-s3 --capabilities CAPABILITY_IAM \
  --parameter-overrides Architecture=arm64 MemoryNamespace=benchmark-arm64 \
  DatabaseSecretArn="$DATABASE_SECRET_ARN"

sam build --template-file infra/aws/template.yaml --use-container \
  --parameter-overrides Architecture=x86_64 MemoryNamespace=benchmark-x86
sam deploy --stack-name labrecall-x86 --resolve-s3 --capabilities CAPABILITY_IAM \
  --parameter-overrides Architecture=x86_64 MemoryNamespace=benchmark-x86 \
  DatabaseSecretArn="$DATABASE_SECRET_ARN"
```

Then compare the endpoints:

```bash
PYTHONPATH=src .venv/bin/python -m labrecall.arm_benchmark \
  --arm-url "$ARM_URL" --x86-url "$X86_URL" \
  --samples 12 --warmups 2 --output evidence/arm-vs-x86.json
```

## Source reuse

- AWS Lambda Power Tuning is used as an external, unmodified measurement workflow; it is
  not vendored or presented as LabRecall code.
- Arm Performix is used as the sponsor-provided profiling tool.
- LabRecall's original application and CockroachDB memory design remain clearly
  attributed in the cross-competition submission.

## Stop conditions

- Do not publish a percentage improvement until both architectures were measured from
  the same commit and region.
- Do not deploy if the dependency build produced wheels for the wrong OS or architecture.
- Do not widen the CockroachDB network allowlist beyond the verified egress boundary.
- Do not leave duplicate benchmark stacks running after evidence capture.
