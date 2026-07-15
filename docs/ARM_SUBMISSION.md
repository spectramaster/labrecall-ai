# Arm Create Devpost submission

> Status: the competition registration and implementation scaffold are complete. Do not
> submit numeric optimization claims until both AWS architectures are measured from the
> same commit and region. Angle-bracket placeholders are hard blockers.

## Project name

LabRecall Arm Evidence Kit

## Tagline

A reproducible Arm64 migration and performance-evidence workflow for production Python
AI agents on AWS Lambda.

## Track

Cloud AI

## Links

- Source: <https://github.com/spectramaster/labrecall-ai>
- Arm64 demo: `<VERIFIED_ARM64_URL>`
- Optional public video: `<VERIFIED_ARM_VIDEO_URL>`
- Raw benchmark evidence: `<VERIFIED_EVIDENCE_PATH_OR_URL>`

## Project overview

AI-agent infrastructure is often declared “Arm-ready” after changing a deployment flag.
That does not prove native dependencies are compatible, the same behavior is preserved,
or the workload is faster or cheaper. LabRecall Arm Evidence Kit turns a real agentic
memory service into a reusable migration and validation workflow: build matching Arm64
and x86_64 Lambda stacks from one commit, isolate their benchmark state, verify runtime
architecture, exercise the full model/vector-database path, and preserve raw evidence
before making an optimization claim.

The reference workload is LabRecall AI, a FastAPI agent that calls Amazon Bedrock and
CockroachDB vector memory. It is intentionally representative of modern Python agents:
native database wheels, serverless cold/warm behavior, outbound model and database calls,
structured API validation, and auditable state.

## Functionality and output

- One parameterized AWS SAM template deploys either `arm64` or `x86_64` from identical
  application code.
- Each stack receives an isolated CockroachDB namespace to prevent benchmark runs from
  learning from or contaminating the other architecture.
- `/health` reports the observed runtime architecture, preventing a mislabeled build.
- The comparison tool sends the same synthetic end-to-end agent workload, excludes
  warmups, and reports success count, mean, median, and p95 latency.
- The report explicitly refuses to treat client HTTPS latency as Lambda billed duration.
- AWS Lambda Power Tuning supplies memory/cost/runtime evidence; Arm Performix supplies
  Arm Neoverse hardware profiling evidence.
- Raw JSON, environment metadata, commit SHA, region, repetitions, and screenshots are
  preserved so another developer can challenge or reproduce the conclusion.

## Why it should win

The project optimizes more than one demo endpoint. It gives Agent developers a concrete
workflow for answering the questions that migration guides often leave implicit:

- Did every native Python dependency build for Linux Arm64?
- Are both architectures running the same commit and functional behavior?
- Is a reported improvement repeatable across median and tail latency?
- Does the cost claim come from billed/runtime evidence rather than network timing?
- Can the Arm-specific bottleneck be located and acted on?

This developer-experience artifact is reusable across many FastAPI, Bedrock, RAG, and
agentic-memory services.

## Setup and validation

Follow `docs/ARM_OPTIMIZATION.md`. The short sequence is:

1. build both architectures in matching Linux containers;
2. deploy separate SAM stacks with `benchmark-arm64` and `benchmark-x86` namespaces;
3. verify `/health` returns `aarch64` and `x86_64` respectively;
4. run the checked-in comparison module with at least three repetitions;
5. run AWS Lambda Power Tuning and export raw results;
6. profile the representative Arm workload with Arm Performix;
7. publish evidence and remove the duplicate benchmark stack.

## Measured results

`<INSERT_VERIFIED_RESULTS_TABLE_AFTER_AWS_DEPLOYMENT>`

Required table columns: architecture, memory, package size, success rate, cold duration,
warm p50, warm p95, billed duration, estimated invocation cost, repetitions, commit SHA,
region, and confidence/caveat notes.

## Open-source reuse

AWS Lambda Power Tuning is used unmodified as an external Apache-2.0 measurement
workflow at pinned revision `572eaf7ac6155c950df358f7cca9a5cb3a247ee9`; its code is
not presented as original LabRecall work. Arm Performix is the sponsor-provided profiler.
All original LabRecall application and benchmark code is MIT licensed.

## Cross-entry disclosure

The underlying LabRecall application was created during the active 2026 contest periods
and is also being prepared for the CockroachDB × AWS Agentic Memory hackathon. The Arm
entry evaluates new Arm-specific migration, compatibility, measurement, and developer
workflow work. It does not present the underlying memory-product concept as the Arm
optimization contribution.

## Built with

`arm64`, `aws-graviton`, `aws-lambda`, `aws-sam`, `lambda-power-tuning`, `arm-performix`,
`amazon-bedrock`, `fastapi`, `python`, `cockroachdb`, `pytest`
