"""Install the two Lightsail runtime secrets without echoing or shell expansion."""

from __future__ import annotations

import getpass
import grp
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from urllib.parse import quote

DATABASE_HOST = "labrecall-memory-29365.j77.aws-us-east-1.cockroachlabs.cloud"
DATABASE_USER = "labrecall_app"
DATABASE_NAME = "defaultdb"
CA_CERT = "/home/ec2-user/.postgresql/root.crt"
ENV_PATH = Path("/etc/labrecall/labrecall.env")


def build_database_url(password: str) -> str:
    """Build a verify-full URL while safely encoding an arbitrary password."""
    encoded_password = quote(password, safe="")
    return (
        f"postgresql://{DATABASE_USER}:{encoded_password}@{DATABASE_HOST}:26257/"
        f"{DATABASE_NAME}?sslmode=verify-full&sslrootcert={CA_CERT}"
    )


def render_environment(database_url: str, bedrock_token: str) -> str:
    """Return the exact root-owned environment file used by systemd."""
    values = {
        "LABRECALL_MODE": "cloud",
        "AWS_REGION": "us-east-1",
        "MEMORY_NAMESPACE": "public-demo",
        "RETRIEVAL_MIN_SIMILARITY": "0.65",
        "DATABASE_URL": database_url,
        "AWS_BEARER_TOKEN_BEDROCK": bedrock_token,
    }
    return "".join(f"{key}={value}\n" for key, value in values.items())


def atomic_install(content: str, destination: Path = ENV_PATH) -> None:
    """Atomically install the environment file as root:ec2-user, mode 0640."""
    destination.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    group_id = grp.getgrnam("ec2-user").gr_gid
    fd, temporary_name = tempfile.mkstemp(prefix=".labrecall.env.", dir=destination.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(fd, 0o640)
        os.fchown(fd, 0, group_id)
        with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        with suppress(OSError):
            os.close(fd)
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Run this helper with sudo so it can protect the environment file.")

    password = getpass.getpass("CockroachDB labrecall_app password: ")
    if not password:
        raise SystemExit("CockroachDB password cannot be empty.")
    bedrock_token = getpass.getpass("Bedrock bearer token: ")
    if not bedrock_token:
        raise SystemExit("Bedrock token cannot be empty.")

    database_url = build_database_url(password)
    atomic_install(render_environment(database_url, bedrock_token))

    password = ""
    bedrock_token = ""
    database_url = ""
    print(f"Installed {ENV_PATH} with owner root:ec2-user and mode 0640.")


if __name__ == "__main__":
    main()
