# Win-oriented project plan

## Product promise

LabRecall helps computational researchers stop rediscovering the same pipeline repairs.
It remembers failures, retrieves analogous cases, proposes a bounded response, and learns
only from confirmed outcomes.

## Acceptance gates

### M0 — compliance and foundation

- [x] Verify current official rules, timing, eligibility, required tools, and deliverables.
- [x] Create an independent repository and disclose related earlier work.
- [x] Freeze a memory-first use case with a human safety boundary.
- [x] Pass offline unit and API tests.

### M1 — memory semantics

- [x] Implement episodic, semantic, outcome, and governance memory.
- [x] Retrieve similar incidents with deterministic local embeddings in fixture mode.
- [x] Require a confirmed outcome before promoting a repair into semantic memory.
- [x] Make every recommendation cite the memory IDs that influenced it.
- [x] Add similarity abstention, outcome-weighted ranking, and visible decision scores.
- [x] Isolate browser demo sessions with hashed CockroachDB namespaces.
- [x] Expose a provenance-safe audit timeline and one-click cold → confirm → recall proof.

### M2 — real CockroachDB integration

- [x] Create a no-card CockroachDB Cloud cluster and least-privilege database user.
- [x] Apply the vector-enabled schema and distributed vector index.
- [x] Run a credentialed `labrecall_app` write → retrieve → outcome → learned-recall proof.
- [ ] Preserve a live read-only MCP inspection transcript (OAuth and tool boundary are configured).
- [x] Run relevant official Agent Skills and record their findings and fixes.

### M3 — AWS application

- [ ] Use Bedrock Titan embeddings and Nova for evidence-bounded explanations.
- [x] Prepare a hardened Lightsail systemd/Nginx deployment with fixed CockroachDB egress.
- [x] Package the same FastAPI service for AWS Lambda/Arm measurement with Mangum.
- [ ] Deploy a free-to-test public endpoint with protected server-side secrets.
- [x] Add rate limits, input bounds, structured errors, logs, and health checks.

### M4 — evaluation and submission

- [x] Build a frozen synthetic benchmark with positive cases, unrelated controls, and
  outcome-calibration checks.
- [x] Compare memory-on versus memory-off retrieval, abstention, latency, consolidation,
  and negative-feedback behavior.
- [ ] Record a real under-three-minute demo showing the CockroachDB memory layer.
- [ ] Publish the deployed app, demo video, and final evidence ledger (code and architecture published).
- [ ] Submit early and verify the final public Devpost page.

## Judge-facing proof

1. Memory design: the app fails its core task if CockroachDB memory is removed.
2. Technical implementation: vector and transactional state share one consistent store;
   MCP/skills evidence demonstrates safe operations.
3. Impact: the benchmark models repeated failures across researchers and sessions.
4. Product readiness: bounded actions, human approval, tenant isolation, audit trails,
   least privilege, and tested recovery paths are visible.
5. Originality: outcome-gated repair learning is not a generic chat-history or RAG demo.
