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

## Native Linux Arm64 CI proof and deployment artifacts

Commit `4f9f979` added a second job on GitHub's hosted `ubuntu-24.04-arm` runner.
Both jobs build the Lambda target on the target CPU, import the native `psycopg-binary`
wheel, run the same package probe, and upload a short-lived deployment artifact. Commit
`59cf41a` changed each artifact to contain the Lambda package directly at the archive
root, added a path-safe SAM installer, and passed the full 12-test suite.

- Latest workflow run: <https://github.com/spectramaster/labrecall-ai/actions/runs/29453587601>
- `package-arm64`: `success`
- Native Arm64 probe:

  ```json
  {"application": "LabRecall AI", "architecture": "aarch64", "psycopg_version": "3.3.4", "static_assets": ["app.css", "app.js", "index.html"]}
  ```

- `verify` (x86_64): `success`
- Uploaded artifacts: `labrecall-linux-arm64` (29,288,672 bytes) and
  `labrecall-linux-x86_64` (27,747,093 bytes)
- Artifact expiry: 2026-07-22 UTC. The workflow can regenerate both from the same commit;
  the archives are deployment inputs, not permanent evidence.

## Remaining evidence

- Deploy the exact target-native archives to their matching Lambda architectures.
- Verify `/health` reports `aarch64` and `x86_64` on the two deployed stacks.
- Run correctness and end-to-end comparison from the same commit and region.
- Capture Lambda Power Tuning and Arm Performix evidence.
