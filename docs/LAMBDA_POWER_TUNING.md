# AWS Lambda Power Tuning evidence procedure

## Reused upstream tool

Use the unmodified Apache-2.0 project
[`alexcasalboni/aws-lambda-power-tuning`](https://github.com/alexcasalboni/aws-lambda-power-tuning)
at commit `572eaf7ac6155c950df358f7cca9a5cb3a247ee9`. The preferred deployment is the
official AWS Serverless Application Repository entry, version 4.4.0, because it avoids
installing another build toolchain and is the upstream project's easiest documented
option.

At deployment, restrict `lambdaResource` to the LabRecall function-name prefix rather
than the upstream default `*`, retain logs for 7 days, and keep the state-machine timeout
at 300 seconds for the bounded first pass.

## Checked-in workload

`evidence/lambda-power-tuning-input.template.json` is a valid API Gateway HTTP API v2
event that exercises the real `POST /api/incidents` Mangum path. A unit test sends the
same payload to the packaged handler. It uses only synthetic data.

The first pass is intentionally bounded:

- 512, 1024, 1536, and 2048 MB;
- five invocations per memory value, the upstream minimum;
- sequential execution because each stack reserves only two concurrent executions;
- balanced cost/speed strategy;
- no automatic configuration change;
- payload logging disabled;
- full per-memory results included in the state-machine output.

Before the first measured run, copy the template and replace only `FUNCTION_ARN`. Run a
single `dryRun: true` execution to verify IAM and payload handling, then remove `dryRun`
for the measured pass. Never edit the committed template with a real account ID or ARN.

## Evidence contract

Run the state machine once for the Arm64 function and once for the x86_64 control from
the same LabRecall commit and AWS region. Preserve the complete Step Functions output as
`evidence/power-tuning-arm64.json` and `evidence/power-tuning-x86_64.json` after checking
that neither contains a secret or account identifier.

Report, for every memory value:

- architecture and exact function version;
- average billed duration and average invocation cost;
- success/failure count;
- Power Tuning execution cost;
- the recommended balanced memory value.

Do not compare client HTTPS latency with Lambda billed duration. Do not claim that Arm64
is faster or cheaper until the two raw outputs are captured and reconciled. Delete the
Power Tuning SAR stack after the final evidence is exported.
