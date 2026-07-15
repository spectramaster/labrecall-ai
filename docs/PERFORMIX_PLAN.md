# Arm Performix measurement plan

Arm Performix needs a Linux target with access to hardware performance counters; AWS
Lambda does not expose that profiling surface. Therefore, Performix evidence must be
clearly labeled as a **representative Graviton CPU profile**, while Lambda Power Tuning
remains the source of serverless billed-duration and cost evidence.

## Target

- AWS EC2 `t4g.small` in `us-east-1` (Graviton2 / Arm Neoverse)
- Amazon Linux quick-start image
- one short-lived instance, terminated immediately after export
- the same LabRecall commit and Python 3.12 dependency set as the Lambda package
- synthetic fixture-mode benchmark only; no database credential on the instance

AWS's current T4g program covers up to 750 `t4g.small` hours per month through
2026-12-31, but surplus CPU credits, storage, and public IPv4 can still incur charges.
The USD 5 AWS budget and an explicit termination check therefore remain mandatory.

## Workload boundary

Profile the deterministic memory-on and memory-off benchmark plus package import. This
isolates CPU, Python runtime, hashing/embedding, serialization, and retrieval behavior
without misrepresenting Bedrock or CockroachDB network latency as a CPU property.

Collect:

- exact instance type, AMI ID, kernel, Python, commit, and CPU identity;
- wall-clock repetitions from `labrecall.benchmark`;
- Performix function hotspots and guided findings;
- machine-readable export and one screenshot of the result;
- any code change motivated by the profile, followed by an identical before/after run.

## Stop conditions

- Do not launch until the AWS budget exists.
- Do not accept an Arm download EULA on behalf of the account owner if the site asks for
  a personal legal acceptance.
- Do not install Performix on the development Mac; use only the short-lived Graviton
  target or a user-scoped archive.
- Do not leave the EC2 instance, disk, security group, key pair, or public IPv4 running
  after the evidence is exported.
- Do not generalize an EC2 microarchitecture result into a Lambda energy claim.
