# CockroachDB submission video script — target 2:40

> The public AWS service is verified. Record with synthetic incidents and hide account
> IDs, URLs containing tokens, cloud credentials, and the AWS Support case page.

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

Show the repository's verified schema/evidence page and the demo's governance timeline.
Never show credentials or account data.

> Incidents, outcomes, repair memories, and governance events are namespace-scoped. The
> application user has only select, insert, and update grants, and the AWS instance is
> the only address allowed to reach CockroachDB.

## 2:03–2:28 — AWS and failure behavior

Show the architecture diagram, then `/health` with `mode=cloud`,
`embedding_provider=hash`, and `architecture=x86_64`.

> Amazon Lightsail hosts the bounded service behind rate-limited HTTPS. Bedrock adapters
> are implemented, but AWS is reviewing an account-level Runtime restriction, so this
> public proof explicitly reports its isolated deterministic embedding provider. It
> never pretends a blocked model call succeeded.

## 2:28–2:40 — close

Show the public repository and test badge.

> LabRecall turns troubleshooting into governed organizational memory: evidence,
> outcomes, confidence, and a repair your next run can trust.
