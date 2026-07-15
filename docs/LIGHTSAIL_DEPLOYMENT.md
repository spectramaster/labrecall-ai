# Cost-bounded Lightsail deployment

This is the primary CockroachDB × AWS hackathon deployment. It keeps CockroachDB's SQL
allowlist narrow by using the existing Lightsail static IPv4 address as the only cloud
egress address. The separate Lambda template remains available for Arm64 measurement,
but it is not required for the public CockroachDB demo.

## Verified target resources

- Instance: `labrecall-free-vps`, Amazon Linux 2023, Oregon (`us-west-2a`)
- Static IPv4: `32.184.180.92`
- CockroachDB allowlist: `labrecall-lightsail-static-ip`, `32.184.180.92/32`
- Instance bundle: USD 7/month with the first-use three-month trial
- Distribution plan: 50 GB Lightsail CDN, free for the first year for eligible accounts

The CDN default domain provides HTTPS. The distribution must use the instance as its
origin and disable caching for dynamic responses. The instance firewall exposes HTTP
80 only after Nginx is installed and the local health check passes. SSH remains
restricted; the browser SSH console is the operator path.

## Secret boundary

The operator enters two values through hidden terminal prompts:

- `DATABASE_URL`: the dedicated least-privilege `labrecall_app` CockroachDB URL;
- `AWS_BEARER_TOKEN_BEDROCK`: a time-limited Bedrock API key created for this synthetic
  hackathon demo.

No secret is committed, printed, copied into screenshots, or passed on a command line.
The values live only in `/etc/labrecall/labrecall.env`, mode `0640`, owned by
`root:ec2-user`. The Bedrock key expires after the judging window and is deleted after
results. AWS documents long-term Bedrock API keys as exploration credentials; this
project uses one only because Lightsail instances do not support service roles. A
production deployment should use short-term credentials on a service that supports an
IAM execution role.

```bash
read -rsp "CockroachDB DATABASE_URL: " DATABASE_URL; echo
read -rsp "Bedrock bearer token: " AWS_BEARER_TOKEN_BEDROCK; echo
printf '%s\n' \
  "LABRECALL_MODE=cloud" \
  "AWS_REGION=us-east-1" \
  "MEMORY_NAMESPACE=public-demo" \
  "RETRIEVAL_MIN_SIMILARITY=0.65" \
  "DATABASE_URL=$DATABASE_URL" \
  "AWS_BEARER_TOKEN_BEDROCK=$AWS_BEARER_TOKEN_BEDROCK" \
  | sudo tee /etc/labrecall/labrecall.env >/dev/null
sudo chown root:ec2-user /etc/labrecall/labrecall.env
sudo chmod 0640 /etc/labrecall/labrecall.env
unset DATABASE_URL AWS_BEARER_TOKEN_BEDROCK
```

## Install and start

Run from the browser SSH terminal after the project branch is pushed:

```bash
cd /home/ec2-user/labrecall-ai
git fetch origin
git checkout codex/labrecall-foundation
git pull --ff-only

python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install .

sudo install -d -m 0750 -o root -g ec2-user /etc/labrecall
sudo install -m 0644 infra/lightsail/labrecall.service \
  /etc/systemd/system/labrecall.service
sudo dnf install -y nginx
sudo install -m 0644 infra/lightsail/labrecall-nginx-zone.conf \
  /etc/nginx/conf.d/labrecall-zone.conf
sudo install -m 0644 infra/lightsail/labrecall-nginx-locations.conf \
  /etc/nginx/default.d/labrecall-locations.conf

sudo systemctl daemon-reload
sudo systemctl enable --now labrecall
curl --fail --silent http://127.0.0.1:8000/health
sudo nginx -t
sudo systemctl enable --now nginx
curl --fail --silent http://127.0.0.1/health
```

Only after both local checks succeed, add TCP 80 to the Lightsail firewall and create a
50 GB distribution with caching disabled. Verify the assigned HTTPS domain through the
full cold → confirm → recall proof before recording it in Devpost.

Run the frozen benchmark against the same Bedrock Titan path used by the application:

```bash
cd /home/ec2-user/labrecall-ai
sudo systemd-run --pipe --wait --collect --uid=ec2-user \
  --working-directory=/home/ec2-user/labrecall-ai \
  --property=EnvironmentFile=/etc/labrecall/labrecall.env \
  --setenv=PYTHONPATH=src \
  /home/ec2-user/labrecall-ai/.venv/bin/python scripts/bedrock_benchmark.py
```

Review the JSON before preserving it. It must keep the eight positive cases, three
unrelated controls, selection threshold, per-case rows, calibration path, and stated
limitations. Do not replace the fixture evidence or claim Titan quality until this
cloud run completes successfully.

## Rollback and cleanup

```bash
sudo systemctl disable --now nginx labrecall
sudo rm -f /etc/labrecall/labrecall.env
sudo systemctl daemon-reload
```

Also close TCP 80, delete the CDN distribution when it is no longer needed, and delete
the Bedrock API key after judging. The zero-spend AWS Budget is an alert, not an
automatic kill switch; review Lightsail billing before the instance trial ends.
