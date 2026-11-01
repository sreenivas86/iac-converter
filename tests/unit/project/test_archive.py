from pathlib import Path
from zipfile import ZipFile

import pytest

import iac_converter.project.archive as archive_module
from iac_converter.project import (
    Project,
    ProjectArchiveError,
    ProjectFile,
    load_project_zip,
    save_project_zip,
)


def test_save_project_zip_writes_files(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content='resource "aws_s3_bucket" "data" {}\n',
            ),
            ProjectFile(
                path="modules/storage/main.tf",
                content="# Nested Terraform\n",
            ),
            ProjectFile(
                path="README.md",
                content="# Example\n",
            ),
        ]
    )

    archive = tmp_path / "project.zip"

    save_project_zip(project, archive)

    assert archive.exists()

    with ZipFile(archive) as zip_file:
        assert sorted(zip_file.namelist()) == [
            "README.md",
            "main.tf",
            "modules/storage/main.tf",
        ]


def test_load_project_zip_reads_files(tmp_path: Path) -> None:
    archive = tmp_path / "project.zip"

    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("main.tf", "# Terraform\n")
        zip_file.writestr(
            "modules/storage/main.tf",
            "# Nested Terraform\n",
        )

    project = load_project_zip(archive)

    assert {project_file.path: project_file.content for project_file in project.files} == {
        "main.tf": "# Terraform\n",
        "modules/storage/main.tf": "# Nested Terraform\n",
    }


def test_project_zip_round_trip(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="# Terraform\n",
            ),
            ProjectFile(
                path="variables.tf",
                content="# Variables\n",
            ),
            ProjectFile(
                path="modules/storage/main.tf",
                content="# Storage\n",
            ),
        ]
    )

    archive = tmp_path / "project.zip"

    save_project_zip(project, archive)

    loaded = load_project_zip(archive)

    assert {project_file.path: project_file.content for project_file in loaded.files} == {
        project_file.path: project_file.content for project_file in project.files
    }


def test_load_project_zip_rejects_missing_archive(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ProjectArchiveError,
        match="does not exist",
    ):
        load_project_zip(tmp_path / "missing.zip")


def test_load_project_zip_rejects_invalid_archive(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "invalid.zip"
    archive.write_text("not a zip file", encoding="utf-8")

    with pytest.raises(
        ProjectArchiveError,
        match="Invalid ZIP",
    ):
        load_project_zip(archive)


def test_save_project_zip_rejects_duplicate_paths(
    tmp_path: Path,
) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="first\n",
            ),
            ProjectFile(
                path="main.tf",
                content="second\n",
            ),
        ]
    )

    with pytest.raises(
        ProjectArchiveError,
        match="Duplicate project file path",
    ):
        save_project_zip(
            project,
            tmp_path / "project.zip",
        )


def test_load_project_zip_rejects_parent_escape(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "unsafe.zip"

    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "../outside.tf",
            "# Must not escape\n",
        )

    with pytest.raises(
        ProjectArchiveError,
        match="unsafe path",
    ):
        load_project_zip(archive)


def test_load_project_zip_rejects_too_many_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive_module, "MAX_ARCHIVE_FILES", 1)

    archive = tmp_path / "too_many_files.zip"

    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("one.tf", "# First\n")
        zip_file.writestr("two.tf", "# Second\n")

    with pytest.raises(
        ProjectArchiveError,
        match="too many files",
    ):
        load_project_zip(archive)


def test_load_project_zip_rejects_oversized_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive_module, "MAX_FILE_SIZE", 4)

    archive = tmp_path / "oversized_file.zip"

    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("large.tf", "12345")

    with pytest.raises(
        ProjectArchiveError,
        match="exceeds the 10 MB limit",
    ):
        load_project_zip(archive)


def test_load_project_zip_rejects_oversized_total_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive_module, "MAX_TOTAL_SIZE", 5)

    archive = tmp_path / "oversized_total.zip"

    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("one.tf", "123")
        zip_file.writestr("two.tf", "456")

    with pytest.raises(
        ProjectArchiveError,
        match="total uncompressed size limit",
    ):
        load_project_zip(archive)


def test_load_project_zip_rejects_duplicate_paths(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "duplicate_paths.zip"

    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("main.tf", "first\n")

        with pytest.warns(UserWarning, match="Duplicate name"):
            zip_file.writestr("main.tf", "second\n")

    with pytest.raises(
        ProjectArchiveError,
        match="duplicate path",
    ):
        load_project_zip(archive)


def test_load_project_zip_enforces_streaming_file_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive_module, "MAX_FILE_SIZE", 4)

    archive_path = tmp_path / "streaming_limit.zip"

    with ZipFile(archive_path, "w") as zip_file:
        zip_file.writestr("large.tf", "1234")

    class OversizedStream:
        def __init__(self) -> None:
            self.chunks = [b"12345", b""]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size: int = -1) -> bytes:
            return self.chunks.pop(0)

    original_open = ZipFile.open

    def fake_open(self, name, mode="r", pwd=None, *, force_zip64=False):
        if mode == "r" and getattr(name, "filename", name) == "large.tf":
            return OversizedStream()

        return original_open(
            self,
            name,
            mode=mode,
            pwd=pwd,
            force_zip64=force_zip64,
        )

    monkeypatch.setattr(ZipFile, "open", fake_open)

    with pytest.raises(
        ProjectArchiveError,
        match="10 MB limit",
    ):
        load_project_zip(archive_path)


def test_load_project_zip_enforces_streaming_total_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive_module, "MAX_TOTAL_SIZE", 5)

    archive_path = tmp_path / "streaming_total_limit.zip"

    with ZipFile(archive_path, "w") as zip_file:
        zip_file.writestr("one.tf", "123")
        zip_file.writestr("two.tf", "456")

    original_open = ZipFile.open

    class OversizedStream:
        def __init__(self, content: bytes) -> None:
            self.content = content

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size: int = -1) -> bytes:
            result = self.content[:size]
            self.content = self.content[size:]
            return result

    def fake_open(self, name, mode="r", pwd=None, *, force_zip64=False):
        filename = getattr(name, "filename", name)

        if mode == "r" and filename == "one.tf":
            return OversizedStream(b"123")

        if mode == "r" and filename == "two.tf":
            return OversizedStream(b"456")

        return original_open(
            self,
            name,
            mode=mode,
            pwd=pwd,
            force_zip64=force_zip64,
        )

    monkeypatch.setattr(ZipFile, "open", fake_open)

    with pytest.raises(
        ProjectArchiveError,
        match="total uncompressed size limit",
    ):
        load_project_zip(archive_path)
