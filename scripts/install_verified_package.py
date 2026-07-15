"""Safely install a CI-built Lambda archive into SAM's generated build directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path


def _validated_build_dir(path: Path) -> Path:
    resolved = path.resolve()
    expected = (Path.cwd() / ".aws-sam" / "build" / "LabRecallApi").resolve()
    if resolved != expected:
        raise ValueError(f"refusing to modify unexpected build directory: {resolved}")
    if not resolved.is_dir():
        raise ValueError("run sam build before installing the verified package")
    return resolved


def _validate_archive(archive: zipfile.ZipFile) -> None:
    for member in archive.infolist():
        path = Path(member.filename)
        mode = member.external_attr >> 16
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive path: {member.filename}")
        if stat.S_ISLNK(mode):
            raise ValueError(f"symbolic links are not accepted: {member.filename}")


def install_package(archive_path: Path, build_dir: Path) -> dict[str, object]:
    archive_path = archive_path.resolve()
    target = _validated_build_dir(build_dir)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="labrecall-package-") as temp_name:
        extracted = Path(temp_name)
        with zipfile.ZipFile(archive_path) as archive:
            _validate_archive(archive)
            archive.extractall(extracted)

        required = [
            extracted / "labrecall" / "app.py",
            extracted / "labrecall" / "static" / "index.html",
            extracted / "psycopg" / "__init__.py",
        ]
        missing = [str(path.relative_to(extracted)) for path in required if not path.is_file()]
        if missing:
            raise ValueError(f"archive is not a LabRecall Lambda package; missing: {missing}")

        for child in target.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        shutil.copytree(extracted, target, dirs_exist_ok=True)

    result: dict[str, object] = {
        "archive": archive_path.name,
        "sha256": digest,
        "target": str(target),
        "files": sum(1 for path in target.rglob("*") if path.is_file()),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=Path(".aws-sam/build/LabRecallApi"),
    )
    args = parser.parse_args()
    print(json.dumps(install_package(args.archive, args.build_dir), sort_keys=True))


if __name__ == "__main__":
    main()
