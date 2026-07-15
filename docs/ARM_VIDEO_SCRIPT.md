# Arm submission video script — target 2:30

> Record after verified dual-stack evidence exists. No percentage appears on screen or
> in narration unless it is reproduced from the checked-in raw evidence.

## 0:00–0:18 — problem

Show the one-line architecture switch, then immediately show the evidence checklist.

> Changing a Lambda architecture field does not prove an AI agent is correctly or
> efficiently optimized for Arm. Native wheels, behavior, latency, and billed cost all
> need evidence.

## 0:18–0:48 — representative workload

Show LabRecall handling a synthetic incident on the Arm64 public endpoint.

> This reference service is a real Python agent path: FastAPI on Lambda, Bedrock model
> calls, CockroachDB vector memory, native database dependencies, and structured audits.

## 0:48–1:15 — controlled comparison

Show the SAM architecture and namespace parameters, both `/health` responses, and the
same commit SHA.

> One template deploys both architectures. Separate namespaces prevent one benchmark
> from learning from the other, and runtime architecture proof catches mislabeled builds.

## 1:15–1:48 — measurements

Run the checked-in comparison and show the raw JSON, Lambda Power Tuning result, and
Arm Performix hotspot view.

> The harness reports success, median, and tail latency, but refuses to call client timing
> billed cost. Cost comes from Lambda runtime evidence; hardware insight comes from
> Performix. Every result records its commit, region, memory, and repetitions.

## 1:48–2:15 — verified outcome

Show the final results table and the specific optimization found. Replace the following
only with verified values:

> On this workload, the Arm64 configuration produced `<VERIFIED_RESULT>`, with
> `<VERIFIED_CAVEAT>`. The raw evidence and reproduction commands are public.

## 2:15–2:30 — reusable value

Show repository documentation and cleanup command.

> The output is not a one-off benchmark. It is a reusable Arm migration and evidence
> workflow for serverless AI agents—and it tells developers when the evidence is not yet
> strong enough to make a claim.
