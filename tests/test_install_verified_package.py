from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.install_verified_package import install_package


def _write_package(path: Path, *, unsafe: bool = False) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("labrecall/app.py", "application = 'LabRecall AI'\n")
        archive.writestr("labrecall/static/index.html", "<title>LabRecall AI</title>\n")
        archive.writestr("psycopg/__init__.py", "__version__ = 'test'\n")
        if unsafe:
            archive.writestr("../escape.txt", "unsafe\n")


def test_installs_only_into_expected_sam_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / ".aws-sam" / "build" / "LabRecallApi"
    target.mkdir(parents=True)
    (target / "old.txt").write_text("old\n")
    archive = tmp_path / "package.zip"
    _write_package(archive)

    result = install_package(archive, target)

    assert result["files"] == 3
    assert (target / "labrecall" / "app.py").is_file()
    assert not (target / "old.txt").exists()


def test_rejects_path_traversal_before_replacing_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / ".aws-sam" / "build" / "LabRecallApi"
    target.mkdir(parents=True)
    sentinel = target / "keep.txt"
    sentinel.write_text("keep\n")
    archive = tmp_path / "unsafe.zip"
    _write_package(archive, unsafe=True)

    with pytest.raises(ValueError, match="unsafe archive path"):
        install_package(archive, target)

    assert sentinel.read_text() == "keep\n"
