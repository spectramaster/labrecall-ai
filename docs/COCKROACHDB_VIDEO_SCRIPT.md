# CockroachDB submission video script — target 2:40

> Record only after the public AWS service and live MCP inspection are verified. Use
> synthetic incidents and hide account IDs, URLs containing tokens, and cloud credentials.

## 0:00–0:15 — hook

On screen: title card, then the public LabRecall interface.

Narration:

> Research teams lose hours solving the same pipeline failure twice. LabRecall is an
> agent that remembers only the repairs that people confirmed actually worked.

## 0:15–0:42 — first incident has no reusable memory

Submit a synthetic warm-restart calibration drift. Show the bounded recommendation,
human-approval badge, and empty evidence state.

> The first incident becomes episodic memory in CockroachDB. With no confirmed analogue,
> the agent abstains from claiming a remembered repair and proposes safe diagnostics.

## 0:42–1:05 — outcome-gated learning

Record the supplied successful outcome. Show memory and audit counters change.

> A repair is not learned from model text. Only this observed, human-confirmed outcome
> can promote it into semantic memory, atomically with its audit evidence.

## 1:05–1:35 — learned recall

Submit the paraphrased repeat. Zoom to the evidence card: repair, similarity, confidence,
and generation path.

> On the next semantically equivalent failure, CockroachDB's distributed vector index
> retrieves the proven repair. Transactional state and embeddings remain in one source
> of truth, so the evidence cannot drift away from its outcome.

## 1:35–2:03 — real memory layer

Show a safe CockroachDB view of the four tables and vector indexes, then a read-only MCP
schema or aggregate inspection. Never show credentials or user data.

> Incidents, outcomes, repair memories, and governance events are namespace-scoped. The
> application user has only select, insert, and update grants. A separate Managed MCP
> auditor is OAuth-scoped to read-only tools.

## 2:03–2:28 — AWS and failure behavior

Show the architecture diagram and AWS Lambda health response with architecture.

> Lambda and API Gateway host the bounded service. Bedrock Titan embeds the incident and
> Nova explains only supplied evidence. If generation fails, the service degrades
> explicitly to deterministic language instead of inventing a repair.

## 2:28–2:40 — close

Show the public repository and test badge.

> LabRecall turns troubleshooting into governed organizational memory: evidence,
> outcomes, confidence, and a repair your next run can trust.
