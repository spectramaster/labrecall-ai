# LabRecall AI

**A research-pipeline repair agent that remembers what actually worked.**

[Public demo](https://32.184.180.92) ·
[2:20 judge video](https://youtu.be/llfCoDkt1DE) ·
[Submission evidence](docs/COCKROACHDB_SUBMISSION.md)

![LabRecall AI project cover](docs/assets/labrecall-cover.png)

![LabRecall AI web interface](docs/assets/labrecall-ui.jpg)

![LabRecall AI architecture](docs/assets/labrecall-architecture.png)

LabRecall turns failed computational-research runs into durable, governed memory.
For each incident it stores structured state and an embedding in CockroachDB, retrieves
semantically similar failures through CockroachDB's distributed vector index, proposes
a bounded repair plan, and learns from the human-confirmed outcome. The public service
is live on a cost-bounded Amazon Lightsail deployment with a fixed database egress IP
and an automatically renewed Let's Encrypt IP certificate. Amazon Bedrock integration
is implemented, but the current public demo explicitly uses an isolated deterministic
embedding fallback while AWS Support reviews an account-wide Runtime restriction.

This is a new project for the 2026 CockroachDB × AWS Build with Agentic Memory
Hackathon. It was started during the official submission period. No ReproFrame source
code was copied into this repository; the separate earlier project is disclosed only
as product-domain context in [`docs/PREEXISTING_WORK.md`](docs/PREEXISTING_WORK.md).

## Why memory is the product

Ordinary troubleshooting chat forgets the environment, repeats rejected advice, and
cannot measure whether a proposed repair worked. LabRecall maintains four linked forms
of memory:

1. episodic memory — exact incident, environment, observations, and attempted actions;
2. semantic memory — vectorized failure signatures and reusable repair lessons;
3. outcome memory — human-confirmed success, failure, side effects, and confidence;
4. governance memory — every retrieval, recommendation, approval, and model/tool call.

CockroachDB is both the transactional source of truth and the vector store. A repair is
never learned unless its outcome is recorded atomically.

Repeated, semantically equivalent successes consolidate into one repair memory instead
of inflating the store. Confirmed failed reuse lowers that memory's calibrated
confidence. Transaction retries use exponential backoff with jitter, while ambiguous
commits are surfaced for operation-ID inspection instead of being blindly replayed.

## Sponsor technology

- **CockroachDB Distributed Vector Indexing:** runtime similarity search over failure
  signatures while keeping transactional state and embeddings consistent.
- **CockroachDB Agent Skills:** the official schema and statement-analysis skills drive
  reproducible database reviews; the pinned source, findings, and fixes are committed in
  the evidence ledger.
- **Amazon Lightsail:** hosts the public FastAPI service behind a fixed egress IP and
  Nginx with an automatically renewed, short-lived Let's Encrypt IP certificate.
- **Amazon Bedrock (integration implemented, account review pending):** Titan and Nova
  adapters are tested without claiming a successful live invocation. The public demo
  reports `embedding_provider=hash` until AWS Support removes the Runtime restriction.
- **AWS Lambda:** the same Mangum package is retained for Arm64 versus x86_64 sponsor
  measurement; it is not required for the primary public demo.

## Local foundation

```bash
uv sync --extra dev --locked
uv run pytest -q
PYTHONPATH=src uv run python -m labrecall.benchmark
PYTHONPATH=src uv run uvicorn labrecall.app:app --reload
```

The default `LABRECALL_MODE=fixture` uses deterministic embeddings and an in-memory
repository. Set `LABRECALL_MODE=cloud`, `DATABASE_URL`, and AWS settings only in a local
`.env` or deployment secret store. Never commit credentials.

The primary Lightsail runtime reads its database URL and Bedrock-specific bearer token
from a root-owned server environment file. The browser never receives either value.
The alternative Lambda template reads the database URL from AWS Secrets Manager at cold
start; CloudFormation receives only the secret ARN.

For a credentialed CockroachDB smoke test without persisting the connection string:

```bash
DATABASE_URL='postgresql://…' PYTHONPATH=src \
  .venv/bin/python scripts/live_cockroach_proof.py
```

## Safety boundary

LabRecall proposes bounded diagnostic steps; it does not execute shell commands or
modify infrastructure. Human approval and an observed outcome are required before a
repair becomes reusable memory. The demo uses synthetic incidents and no personal or
proprietary research data.

Official-rule verification and build gates are recorded in
[`docs/OFFICIAL_RULES.md`](docs/OFFICIAL_RULES.md) and
[`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md). Open-source attribution and the live
database proof are recorded in [`docs/OPEN_SOURCE_REUSE.md`](docs/OPEN_SOURCE_REUSE.md)
and [`docs/CLOUD_EVIDENCE.md`](docs/CLOUD_EVIDENCE.md).
The pinned official Agent Skills review is in
[`docs/SKILL_EVIDENCE.md`](docs/SKILL_EVIDENCE.md).
The deployable system boundary and trust model are in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
The reproducible Arm64 migration and dual-architecture evidence contract is in
[`docs/ARM_OPTIMIZATION.md`](docs/ARM_OPTIMIZATION.md).
Native-package compatibility evidence is in
[`docs/ARM_EVIDENCE.md`](docs/ARM_EVIDENCE.md).
The credential-safe, cost-bounded CloudShell deployment procedure is in
[`docs/AWS_DEPLOYMENT_RUNBOOK.md`](docs/AWS_DEPLOYMENT_RUNBOOK.md).
The fixed-egress public deployment is in
[`docs/LIGHTSAIL_DEPLOYMENT.md`](docs/LIGHTSAIL_DEPLOYMENT.md).
The sponsor-grade measurement boundaries are in
[`docs/LAMBDA_POWER_TUNING.md`](docs/LAMBDA_POWER_TUNING.md) and
[`docs/PERFORMIX_PLAN.md`](docs/PERFORMIX_PLAN.md).
Judge-ready drafts and timed demo scripts are in
[`docs/COCKROACHDB_SUBMISSION.md`](docs/COCKROACHDB_SUBMISSION.md),
[`docs/COCKROACHDB_VIDEO_SCRIPT.md`](docs/COCKROACHDB_VIDEO_SCRIPT.md),
[`docs/ARM_SUBMISSION.md`](docs/ARM_SUBMISSION.md), and
[`docs/ARM_VIDEO_SCRIPT.md`](docs/ARM_VIDEO_SCRIPT.md). Hard placeholders remain until
the corresponding live cloud evidence is verified.

## Read-only Managed MCP auditor

Trusted Codex clients can load the project-scoped `.codex/config.toml` and authenticate
with CockroachDB Cloud OAuth. The committed allowlist exposes only read-oriented schema,
query, and plan-inspection tools; database-creation and insert tools are not enabled.

```bash
codex mcp login --scopes mcp:read cockroachdb-cloud
codex mcp get cockroachdb-cloud
```

OAuth tokens stay in the local Codex credential store and are never committed. A new
trusted Codex session is required after changing MCP configuration; the current client
cannot hot-load a newly added server.
