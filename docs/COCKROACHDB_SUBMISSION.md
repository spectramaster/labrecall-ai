# CockroachDB × AWS Devpost submission

> Status: judge-ready copy and the functional AWS URL are verified. The public video URL
> must be inserted only after the final under-three-minute recording is published.

## Project name

LabRecall AI

## Tagline

An agent that remembers which research-pipeline repairs actually worked—and learns only
from human-confirmed outcomes.

## Links

- Source: <https://github.com/spectramaster/labrecall-ai>
- Functional demo: <https://32.184.180.92>
- Public video under three minutes: `<VERIFIED_YOUTUBE_URL>`

## Inspiration

Computational researchers repeatedly lose time to the same failures: a checkpoint is
written non-atomically, a calibration drifts after restart, a dependency changes random
seeds, or a feature schema no longer matches inference. Ordinary troubleshooting chat
can suggest an answer, but it forgets the environment, cannot distinguish advice from a
repair that really worked, and may confidently repeat a failed action.

LabRecall starts from a stricter question: what if the memory—not the chat interface—were
the product?

## What it does

LabRecall converts each failed run into four linked forms of durable memory:

1. **Episodic memory** preserves the exact incident, environment, constraints, and
   attempted actions.
2. **Semantic memory** retrieves analogous, confirmed repairs through CockroachDB's
   distributed vector index.
3. **Outcome memory** records what the researcher actually tried and whether it worked,
   failed, or partially worked.
4. **Governance memory** records retrievals, recommendations, confirmations, promotions,
   model paths, and evidence IDs.

The agent proposes a bounded diagnostic plan and cites every remembered repair that
influenced it. A repair cannot become reusable memory until a person records a confirmed
successful outcome. Repeated successes consolidate confidence; confirmed failures reduce
it. LabRecall never executes the proposed shell or infrastructure changes itself.

## How we built it

CockroachDB is both the transactional system of record and the vector store. Incidents,
outcomes, repair memories, and audit events share one consistency boundary, avoiding the
drift that appears when operational state and embeddings live in separate databases.
The live Basic cluster uses namespace-scoped rows, least-privilege SQL, TLS, and no
`0.0.0.0/0` network rule.

The public AWS service runs FastAPI on Amazon Lightsail behind Nginx. The instance's
fixed IPv4 is the only cloud address in CockroachDB's SQL allowlist, and a short-lived
Let's Encrypt IP certificate supplies an automatically renewed HTTPS testing URL without
adding a paid CDN. The live app currently uses an explicit deterministic embedding
provider after AWS confirmed an account-wide Bedrock Runtime restriction. Provider names
are part of CockroachDB namespaces, so fallback vectors cannot mix with future Titan
vectors. The database URL and time-bounded Bedrock exploration key stay in a root-owned
server file and are removed after judging.

## CockroachDB tools used

### Distributed Vector Indexing

The agent stores normalized embeddings beside transactional memory and performs
namespace-scoped cosine retrieval through distributed vector indexes. This is on the
runtime path: remove vector recall and the agent loses its ability to reuse proven
repairs.

### Agent Skills repository

The official skills repository is pinned as a Git submodule. Its transaction, SQL, and
security guidance was used as a reproducible engineering review gate; findings and the
resulting fixes are preserved in `docs/SKILL_EVIDENCE.md`.

## AWS services used

- **Amazon Lightsail:** fixed-egress application hosting on the first-use instance trial.
- **Nginx + Let's Encrypt:** rate-limited HTTPS with an automatically renewed IP
  certificate.
- **Lightsail monitoring:** instance and public request/health evidence.

The repository also includes Bedrock Titan and Nova adapters. They are not claimed as a
successful live service in this submission: AWS Support case `178416243800034` is
reviewing the account-wide `ValidationException: Operation not allowed` response.

## Challenges we ran into

CockroachDB Cloud correctly rejected a managed-cluster setting that is not permitted to
application users, so the migration was changed to rely on the platform's current vector
support rather than requesting elevated cluster configuration. We also treated retry
behavior as a correctness problem: serialization failures replay a short transaction
with jitter, while an ambiguous commit is surfaced for operation-ID inspection instead
of being blindly replayed.

The most important product challenge was resisting generic “RAG with chat history.” The
memory model had to preserve outcomes, confidence, idempotency, and governance evidence
without allowing model text to become truth automatically.

AWS Bedrock failed identically through Boto3, direct bearer HTTPS, two regions, and the
account-owner Playground. Rather than conceal the failure or block the demo, we isolated
a deterministic embedding provider in its own namespace, documented the evidence, and
opened a support case. The public health endpoint exposes the active provider.

## Accomplishments

- A real least-privilege CockroachDB client completed write → retrieve → confirmed
  outcome → memory promotion → learned recall.
- The public HTTPS proof recalled the confirmed repair at cosine similarity `0.823063`.
- Four memory types share a single transactional and vector-capable database.
- A one-click isolated proof visibly demonstrates cold abstention, human promotion,
  paraphrased recall, provenance IDs, confidence, and the ordered audit trail.
- Browser sessions map to hashed database namespaces, so public tests do not contaminate
  one another.
- The public service has bounded inputs, request IDs, safe errors, security headers,
  throttling, concurrency limits, deterministic degradation, and readiness checks.
- The synthetic benchmark separates retrieval quality from generation and reports
  memory-on versus memory-off behavior without presenting fixture embeddings as model
  quality.
- Twenty-one automated tests and Ruff currently pass from a clean public repository.

## What we learned

Production memory is not a transcript. It is evidence with provenance, outcomes,
confidence, isolation, and a policy for when experience is allowed to affect the next
decision. CockroachDB is valuable here because the operational event and the semantic
memory do not have to cross an eventual-consistency boundary.

## What's next

Next steps include organization-scoped authentication, richer outcome calibration,
larger multi-researcher evaluation, regional deployment, reviewer queues for memory
promotion, and automated retention controls for sensitive scientific environments.

## Built with

`cockroachdb`, `vector-search`, `agent-skills`, `aws-lightsail`, `nginx`,
`amazon-bedrock`, `fastapi`, `python`, `pytest`

## Testing instructions

1. Open <https://32.184.180.92>; no account or credential should be required.
2. Select **Run the 20-second proof**.
3. Verify the three completed stages: cold abstention, human-confirmed promotion, and
   paraphrased warm recall.
4. Inspect the evidence card for memory ID, similarity, calibrated confidence, decision
   score, and the confirmed repair.
5. Inspect the governance timeline for the ordered incident, retrieval, recommendation,
   outcome, and promotion events.
6. Optionally submit another supplied synthetic incident and record its outcome.
7. The demo contains synthetic data only. Do not enter personal, confidential, or
   proprietary research information.

## Optional product feedback

The Managed MCP read-only default and OAuth scope model are strong foundations for a
separate audit agent. The developer experience would be even clearer if the client CLI
listed the effective OAuth scopes and project-level tool allowlist together, and if the
Cloud console exported a ready-to-commit read-only configuration without any credential
material.
