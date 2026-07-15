# Cloud evidence ledger

## 2026-07-16 — CockroachDB Cloud proof

- Cluster: `labrecall-memory`
- Plan/provider/region: Basic / AWS / N. Virginia (`us-east-1`)
- Cost guardrail: $15 monthly hard limit; $0 due at creation; no payment method added
- SQL user: `labrecall_app`
- Granted privileges: `SELECT`, `INSERT`, and `UPDATE` only on the four application tables
- Network: removed the default `0.0.0.0/0` rule; the AWS allowlist contains only the
  Lightsail static IPv4 `32.184.180.92/32` under
  `labrecall-lightsail-static-ip`
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

- Start a fresh trusted Codex session and preserve one live read-only MCP inspection
  transcript. The server configuration and OAuth authorization are already complete,
  but the client that performed setup cannot hot-load a new MCP server.
- Run the pinned official transaction, SQL, and cloud-security Agent Skills.
- Deploy the public FastAPI service to the existing Lightsail instance, create the
  first-year-free 50 GB distribution, and verify its default HTTPS domain.
- Create a time-bounded Bedrock API key for the synthetic demo, store it only in the
  root-owned server environment file, and delete it after judging.

## 2026-07-16 — Managed MCP access boundary

- Server: official CockroachDB Cloud Managed MCP endpoint
- Authentication: OAuth completed with only the `mcp:read` scope
- Project routing: the committed non-secret cluster ID targets `labrecall-memory`
- Tool boundary: `.codex/config.toml` allowlists cluster/schema inspection, read-only
  queries, query plans, and running-query inspection; mutation tools are excluded
- Credential boundary: the OAuth token remains in the local Codex credential store and
  no token or database credential is present in the repository
- Verification boundary: authorization and configuration are proven; a live MCP tool
  transcript remains pending because this already-running client cannot hot-load the
  newly added server
