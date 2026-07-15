# Cloud evidence ledger

## 2026-07-16 — CockroachDB Cloud proof

- Cluster: `labrecall-memory`
- Plan/provider/region: Basic / AWS / N. Virginia (`us-east-1`)
- Cost guardrail: $15 monthly hard limit; $0 due at creation; no payment method added
- SQL user: `labrecall_app`
- Granted privileges: `SELECT`, `INSERT`, and `UPDATE` only on the four application tables
- Network: removed the default `0.0.0.0/0` rule; only the current development device is
  allowlisted while the AWS egress design is pending
- Tables: `incidents`, `outcomes`, `repair_memories`, `audit_events`
- Vector indexes: `incidents_embedding_idx`, `repair_memories_embedding_idx`
- Browser-shell synthetic proof: inserted one incident, confirmed outcome, promoted
  repair memory, and retrieved it with cosine similarity `1.000000`
- Least-privilege client proof: `scripts/live_cockroach_proof.py` connected as
  `labrecall_app`, wrote two incidents and one outcome, promoted one reusable memory,
  produced four audit events, and recalled the repair at similarity `0.737865` with
  calibrated confidence `0.666667`
- Data boundary: the proof uses synthetic calibration-drift text only; no private or
  proprietary research data was uploaded

The CockroachDB browser SQL shell showed both vector indexes and the limited grants.
The original migration's cluster-setting statement was rejected by managed cloud as a
disallowed statement, so the migration now relies on vector indexing being enabled by
default on current Basic clusters.

## Pending cloud evidence

- Connect the official Managed MCP auditor with read-only scope.
- Run the pinned official transaction, SQL, and cloud-security Agent Skills.
- Deploy the Lambda package after the AWS account owner completes console sign-in.
- Add only the final AWS egress CIDR to the allowlist before cloud runtime verification.
