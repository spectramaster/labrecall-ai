# AWS deployment runbook

This runbook deliberately keeps AWS credentials and the CockroachDB connection string
out of the repository, GitHub Actions, local shell history, and screenshots. The target
region is `us-east-1`, where both declared Bedrock models are available.

## Operator-only gates

The account owner must complete these two actions in the browser:

1. Sign in to the AWS console. Do not create or export a long-lived access key.
2. In Secrets Manager, create a JSON secret named `labrecall/database-url` with one key,
   `DATABASE_URL`, and paste the dedicated `labrecall_app` CockroachDB connection string
   as its value. Do not reveal the value in CloudShell or a recording.

Everything after those gates can run in AWS CloudShell, which is pre-authenticated and
has AWS CLI and AWS SAM CLI installed. Nothing needs to be installed globally on the
development Mac.

## Cost and safety gate

Before deployment:

- create a monthly AWS Budget of USD 5 with actual and forecast alerts;
- keep the Lambda reserved concurrency at 2 and HTTP API throttle at 5 requests/second;
- keep CloudWatch logs for 7 days;
- use only the dedicated least-privilege database user and the two declared Bedrock
  model ARNs;
- never put real research, personal, or confidential data in the demo cluster;
- record the stack outputs so the emergency concurrency kill switch can be used.

The CockroachDB Basic cluster currently accepts only an approved development network.
Lambda does not have a stable public egress IP by default. Two valid choices remain:

1. **Hackathon demo:** temporarily allow `0.0.0.0/0` for SQL only, never for the DB
   console, while retaining TLS, SCRAM authentication, least privilege, the USD 15 hard
   cluster cap, and synthetic data. Remove the rule immediately after judging.
2. **Hardened network:** use static AWS egress or CockroachDB private connectivity. This
   adds infrastructure and cost and is unnecessary for a synthetic short-lived demo.

Do not change the allowlist until the account owner explicitly approves one choice.

## Preflight in AWS CloudShell

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
aws sts get-caller-identity
aws bedrock get-foundation-model \
  --model-identifier amazon.titan-embed-text-v2:0 >/dev/null
aws bedrock get-foundation-model \
  --model-identifier amazon.nova-lite-v1:0 >/dev/null
sam --version

git clone --branch codex/labrecall-foundation \
  https://github.com/spectramaster/labrecall-ai.git
cd labrecall-ai
sam validate --lint --template-file infra/aws/template.yaml

export DATABASE_SECRET_ARN="$(aws secretsmanager describe-secret \
  --secret-id labrecall/database-url --query ARN --output text)" # pragma: allowlist secret
test "$DATABASE_SECRET_ARN" != "None" # pragma: allowlist secret
```

The last command reads only secret metadata, not the secret value.

## Obtain target-native packages

Open the latest successful `ci` run on GitHub and download both artifacts:

- `labrecall-linux-arm64`
- `labrecall-linux-x86_64`

Upload the two downloaded ZIP files to CloudShell. The workflow builds each package on
its target CPU and the archive root directly contains `labrecall/`, `psycopg/`, and the
remaining runtime dependencies. If the artifacts expired, re-run the workflow; never
substitute an archive built for the other architecture.

## Deploy Arm64

```bash
sam build --template-file infra/aws/template.yaml \
  --parameter-overrides Architecture=arm64 MemoryNamespace=benchmark-arm64
python scripts/install_verified_package.py "$HOME/labrecall-linux-arm64.zip"
sam deploy --template-file .aws-sam/build/template.yaml \
  --stack-name labrecall-arm64 --resolve-s3 --capabilities CAPABILITY_IAM \
  --region us-east-1 --no-confirm-changeset --no-fail-on-empty-changeset \
  --parameter-overrides Architecture=arm64 MemoryNamespace=benchmark-arm64 \
  DatabaseSecretArn="$DATABASE_SECRET_ARN"
```

## Deploy x86_64 control

```bash
sam build --template-file infra/aws/template.yaml \
  --parameter-overrides Architecture=x86_64 MemoryNamespace=benchmark-x86
python scripts/install_verified_package.py "$HOME/labrecall-linux-x86_64.zip"
sam deploy --template-file .aws-sam/build/template.yaml \
  --stack-name labrecall-x86 --resolve-s3 --capabilities CAPABILITY_IAM \
  --region us-east-1 --no-confirm-changeset --no-fail-on-empty-changeset \
  --parameter-overrides Architecture=x86_64 MemoryNamespace=benchmark-x86 \
  DatabaseSecretArn="$DATABASE_SECRET_ARN"
```

## Verify before publishing

For each stack, read `ApiUrl`, `Architecture`, `MemoryNamespace`, and `FunctionName` from
CloudFormation outputs. Do not record a successful deployment until all gates pass:

1. `/health` returns `status=ok`, `mode=cloud`, and the expected runtime architecture;
2. `/ready` can open the CockroachDB store;
3. a synthetic incident can be written, confirmed, and recalled;
4. both stacks are from the same Git commit and use isolated namespaces;
5. logs contain no secret value or personal data;
6. the checked-in benchmark writes raw JSON and completes three repetitions.

## Emergency kill switch and cleanup

Set a function's reserved concurrency to zero if invocation volume is unexpected:

```bash
aws lambda put-function-concurrency --function-name FUNCTION_NAME \
  --reserved-concurrent-executions 0
```

After evidence capture and judging, delete the comparison stacks and the temporary
CockroachDB network rule. Keep the repository and evidence, but delete the downloaded
archives from CloudShell and rotate or delete the database secret when it is no longer
needed.

```bash
sam delete --stack-name labrecall-x86 --region us-east-1 --no-prompts
sam delete --stack-name labrecall-arm64 --region us-east-1 --no-prompts
```
