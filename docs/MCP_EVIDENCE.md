# Managed MCP evidence

## Access design

LabRecall uses the official CockroachDB Cloud Managed MCP server as a separately
authenticated operations auditor. It is not part of the public application request
path and cannot alter application data through the committed project configuration.

The project-scoped `.codex/config.toml` targets the non-secret LabRecall cluster ID and
allows only these read-oriented tools:

- cluster, database, table, and schema inspection;
- `SELECT` queries and query-plan inspection;
- running-query inspection.

Creation, mutation, and deletion tools are deliberately absent. OAuth was authorized
with the single `mcp:read` scope on 2026-07-16. Tokens remain in the local Codex
credential store rather than the repository.

## Reproduction

From a trusted Codex project session:

```bash
codex mcp login --scopes mcp:read cockroachdb-cloud
codex mcp get cockroachdb-cloud
```

Restart the Codex project session after adding or changing an MCP server. The setup
client cannot hot-load a newly configured server.

## Evidence status

Configuration and least-scope OAuth authorization are complete. A fresh-session live
inspection transcript is still pending and must not be described as completed until a
read-only tool call returns the targeted cluster schema successfully.
