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

## 2026-07-16 — Public Lightsail HTTPS proof

- Runtime: Amazon Linux 2023 Lightsail, `us-west-2a`, x86_64, static IPv4
  `32.184.180.92`
- Public endpoint: `https://32.184.180.92`
- TLS: Let's Encrypt short-lived IP certificate with a successful renewal dry run and
  a twice-daily systemd renewal timer
- `GET /health`: HTTP 200, `mode=cloud`, `architecture=x86_64`
- `GET /ready`: HTTP 200 after a live CockroachDB `SELECT 1`; the response showed an
  empty isolated public-demo namespace rather than fixture data
- Network boundary: CockroachDB lists the exact `32.184.180.92/32` allowlist entry;
  public HTTP/HTTPS expose only Nginx, while the application listens on localhost
- Secret boundary: database and Bedrock credentials remain in a root-owned `0640`
  environment file and were entered only through hidden prompts

## 2026-07-16 — Bedrock account restriction and recovery case

- Models verified in the official `us-east-1` catalog:
  `amazon.titan-embed-text-v2:0` and `amazon.nova-lite-v1:0`
- A 90-day long-term Bedrock API key is active, directly attached to the AWS-managed
  `AmazonBedrockLimitedAccess` policy; the superseded key and IAM user were deleted
- Invocation failed identically through Boto3, direct HTTPS Bearer authentication, and
  the account-owner Bedrock Playground, across both `us-east-1` and `us-west-2`
- The exact service response is `ValidationException: Operation not allowed`; no API
  key, account credential, or private input was included in the evidence
- Lightsail exposes an internal IAM-role credential before the bearer provider. A
  credential-isolated test set `AWS_EC2_METADATA_DISABLED=true`; the same response
  proved that the remaining blocker is account-wide rather than SDK credential order
- AWS Knowledge Center classifies this exact response as an account security restriction
  requiring AWS Support. Basic Support case `178416243800034` was submitted with the
  full non-secret reproduction matrix and a request to enable Bedrock Runtime inference
- Until AWS removes the restriction, the public service uses the explicit
  `EMBEDDING_PROVIDER=hash` degraded mode in a separate CockroachDB namespace. This keeps
  the real transactional/vector-memory demo testable without claiming a Bedrock run.
  Switching back to `bedrock` cannot mix the two vector spaces because provider names
  are part of the namespace.

## Pending cloud evidence

- Start a fresh trusted Codex session and preserve one live read-only MCP inspection
  transcript. The server configuration and OAuth authorization are already complete,
  but the client that performed setup cannot hot-load a new MCP server.
- Run the pinned official transaction, SQL, and cloud-security Agent Skills.
- Re-test Titan and Nova after AWS resolves support case `178416243800034`, switch
  `EMBEDDING_PROVIDER` from `hash` to `bedrock`, and preserve the frozen benchmark JSON.

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
