# Arm and cross-architecture evidence ledger

## 2026-07-16 — Linux Arm64 package import

- Host: Apple Silicon development machine
- Docker server: `29.6.1`, architecture `aarch64`
- Container platform: `linux/arm64`
- Base image: official `python:3.12-slim`
- Package procedure: installed `requirements-lambda.txt` into a clean temporary target,
  copied only `src/labrecall`, and imported the packaged application through that target
- Observed runtime: `aarch64`
- Native dependency: `psycopg 3.3.4`
- Application import: `LabRecall AI`
- Result: passed

The container was ephemeral, the repository mount was read-only, and no cloud credential
was available inside it.

## Linux x86_64 package proof

The public GitHub Actions runner is an actual `ubuntu-latest` x86_64 environment. CI
builds a fresh Lambda target from `requirements-lambda.txt`, copies the application, and
runs `scripts/package_probe.py` through only the packaged target. The first successful
cross-architecture proof completed from commit `5bb6d14`:

- Workflow run: <https://github.com/spectramaster/labrecall-ai/actions/runs/29452817397>
- Job: `verify` (`success`)
- Step: `Build and import the Linux x86_64 Lambda package` (`success`)
- Probe output:

  ```json
  {"application": "LabRecall AI", "architecture": "x86_64", "psycopg_version": "3.3.4", "static_assets": ["app.css", "app.js", "index.html"]}
  ```

## Remaining evidence

- Build in AWS Lambda's architecture-matched SAM container.
- Verify `/health` reports `aarch64` and `x86_64` on the two deployed stacks.
- Run correctness and end-to-end comparison from the same commit and region.
- Capture Lambda Power Tuning and Arm Performix evidence.
