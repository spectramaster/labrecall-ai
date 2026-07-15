# Open-source reuse and attribution

LabRecall is original application code. We evaluated established open-source work to
reuse operational knowledge and avoid rebuilding sponsor tooling. No third-party source
code was copied into `src/labrecall`.

## Adopted directly

| Project | License | Pinned revision | How it is used |
| --- | --- | --- | --- |
| [cockroachlabs/cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills) | Apache-2.0 | `9e73c9d45894449490c23ce90d18e6f233251dfa` | Pinned Git submodule. Its transaction, SQL, and cloud-security skills define review gates and evidence templates. |

The submodule preserves upstream history and license. It is not bundled into the
application runtime.

## Studied, not copied

| Project | License | Revision reviewed | Design lesson applied |
| --- | --- | --- | --- |
| [JordanMcCann/agentmemory](https://github.com/JordanMcCann/agentmemory) | MIT | `3aa3b8389896f81dd813fdf9176ef3ca122d809e` | Validate writes, consolidate near-duplicates, calibrate confidence from outcomes, and evaluate recall separately from generation. |
| [aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp](https://github.com/aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp) | MIT-0 | `7a9e70f3abc879b736f0011657462023746f0c36` | Keep AWS infrastructure explicit, secrets server-side, model permissions narrow, and the browser client separated from cloud credentials. |
| [alexcasalboni/aws-lambda-power-tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) | Apache-2.0 | `572eaf7ac6155c950df358f7cca9a5cb3a247ee9` | Use the upstream Step Functions workflow after AWS deployment to measure cost and duration across Lambda memory configurations. No source is vendored or copied. |

## Decisions

- We use CockroachDB as both transactional truth and vector memory, rather than adding
  a second memory database from the reference projects.
- Transaction retries use exponential backoff with jitter. An ambiguous commit is not
  blindly replayed; the application raises an explicit error unless the operation is
  provably idempotent.
- Repair memories are learned only from human-confirmed outcomes. Near-duplicate
  successful repairs consolidate; confirmed failed reuse lowers confidence.
- Evaluation reports retrieval precision/recall and memory-on versus memory-off behavior.
  Fixture embeddings are explicitly not presented as model-quality evidence.
