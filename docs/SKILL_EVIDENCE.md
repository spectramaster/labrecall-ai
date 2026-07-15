# Official CockroachDB Agent Skills evidence

Pinned source: `third_party/cockroachdb-skills` at
`9e73c9d45894449490c23ce90d18e6f233251dfa`.

## designing-application-transactions — PASS with documented boundary

- Transactions are short and do not include network/model calls.
- SQLSTATE `40001` is retried as a full transaction with exponential backoff and jitter.
- SQLSTATE `40003` is not blindly replayed. The code raises `AmbiguousCommitError` unless
  the operation is explicitly idempotent.
- Caller-supplied incident IDs and deterministic audit IDs make incident creation safe to
  retry; outcomes use a unique incident key and reject conflicting evidence.
- Outcome, confidence update, memory promotion, and audit evidence share one transaction.

## cockroachdb-sql — PASS for the current synthetic scale

- Schema applied successfully to CockroachDB Cloud Basic.
- Both `VECTOR(1024)` indexes were verified with `SHOW INDEX`.
- A namespace-prefixed cosine query returned the expected synthetic repair at similarity
  `1.000000`.
- Primary/foreign keys and status checks enforce core invariants in SQL.
- `EXPLAIN` and load-sensitive index tuning remain a pre-production gate once the
  benchmark contains enough rows for a representative plan.

## auditing-cloud-cluster-security — PASS for development

- TLS is required by CockroachDB Cloud; no certificate bypass is configured.
- The default `0.0.0.0/0` allowlist entry was removed.
- Only the current development device is allowlisted; the future AWS runtime must add a
  narrowly scoped egress CIDR rather than restoring allow-all.
- `labrecall_app` has only `SELECT`, `INSERT`, and `UPDATE` on application tables.
- No credentials are committed; `.env` and deployment configuration are ignored.
- Cluster spend is capped at $15/month, with $0 due at creation and no payment method
  added.

These are development-stage checks, not a production compliance certification.
