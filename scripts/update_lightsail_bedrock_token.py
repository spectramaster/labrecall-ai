"""Replace only the Bedrock bearer token in the protected Lightsail environment."""

from __future__ import annotations

import getpass
import grp
import os
import tempfile
from contextlib import suppress
from pathlib import Path

ENV_PATH = Path("/etc/labrecall/labrecall.env")
TOKEN_KEY = "AWS_BEARER_TOKEN_BEDROCK"


def replace_token(content: str, token: str) -> str:
    """Replace exactly one token line without changing any other setting."""
    lines = content.splitlines(keepends=True)
    indexes = [index for index, line in enumerate(lines) if line.startswith(f"{TOKEN_KEY}=")]
    if len(indexes) != 1:
        raise ValueError(f"expected exactly one {TOKEN_KEY} entry")
    newline = "\n" if lines[indexes[0]].endswith("\n") else ""
    lines[indexes[0]] = f"{TOKEN_KEY}={token}{newline}"
    return "".join(lines)


def atomic_install(content: str, destination: Path = ENV_PATH) -> None:
    """Atomically preserve the root:ec2-user, 0640 environment-file boundary."""
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
    if not ENV_PATH.is_file():
        raise SystemExit(f"Missing {ENV_PATH}; run configure_lightsail_secrets.py first.")

    token = getpass.getpass("New Bedrock bearer token: ")
    if not token:
        raise SystemExit("Bedrock token cannot be empty.")

    updated = replace_token(ENV_PATH.read_text(encoding="utf-8"), token)
    atomic_install(updated)
    token = ""
    updated = ""
    print(f"Updated {TOKEN_KEY} in {ENV_PATH}; all other settings were preserved.")


if __name__ == "__main__":
    main()
