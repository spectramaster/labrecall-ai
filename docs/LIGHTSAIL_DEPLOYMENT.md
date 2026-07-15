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
- HTTPS: Let's Encrypt short-lived IP certificate, automatically renewed twice daily

The account's console prices the smallest Lightsail CDN plan at USD 2.50/month, so this
deployment does not create it. Let's Encrypt has generally available IP certificates;
Certbot 5.4 requests the required `shortlived` profile and renews the six-day certificate
automatically. The instance firewall exposes HTTP 80 only after Nginx is installed and
the local health check passes, then exposes HTTPS 443 after the certificate and TLS
configuration validate. SSH remains restricted; the browser SSH console is the operator
path.

## Secret boundary

The operator enters two values through hidden terminal prompts in
`scripts/configure_lightsail_secrets.py`:

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

The helper accepts the dedicated SQL user's password rather than a hand-built URL. It
URL-encodes arbitrary password characters, pins `sslmode=verify-full` and the downloaded
CockroachDB CA certificate, then atomically installs the environment file. Neither
secret appears in shell history, process arguments, or terminal output.

```bash
sudo .venv/bin/python scripts/configure_lightsail_secrets.py
sudo systemctl restart labrecall
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
sudo install -d -m 0755 /var/www/letsencrypt/.well-known/acme-challenge

sudo systemctl daemon-reload
sudo systemctl enable --now labrecall
curl --fail --silent http://127.0.0.1:8000/health
sudo nginx -t
sudo systemctl enable --now nginx
curl --fail --silent http://127.0.0.1/health
```

Only after both local checks succeed, add TCP 80 to the Lightsail firewall and verify
`http://32.184.180.92/health`. Install Certbot 5.4 in an isolated Python 3.11 environment
and request the production certificate:

```bash
sudo /home/ec2-user/labrecall-ai/.venv/bin/python -m venv /opt/certbot311
sudo /opt/certbot311/bin/pip install certbot==5.4.0
sudo /opt/certbot311/bin/certbot certonly \
  --preferred-profile shortlived \
  --webroot --webroot-path /var/www/letsencrypt \
  --ip-address 32.184.180.92 \
  --non-interactive --agree-tos --register-unsafely-without-email

sudo install -m 0644 infra/lightsail/labrecall-nginx-tls.conf \
  /etc/nginx/conf.d/labrecall-tls.conf
sudo install -m 0644 infra/lightsail/labrecall-certbot.service \
  /etc/systemd/system/labrecall-certbot.service
sudo install -m 0644 infra/lightsail/labrecall-certbot.timer \
  /etc/systemd/system/labrecall-certbot.timer
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now labrecall-certbot.timer
sudo systemctl reload nginx
```

Add TCP 443 only after `nginx -t` succeeds. Verify
`https://32.184.180.92/health`, inspect the certificate expiry, and confirm that the
renewal timer is active. Then run the full cold → confirm → recall proof before recording
the URL in Devpost.

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

Also close TCP 80 and 443, remove the certificate-renewal timer, and delete the Bedrock
API key after judging. No CDN distribution is required. The zero-spend AWS Budget is an
alert, not an automatic kill switch; review Lightsail billing before the instance trial
ends.
