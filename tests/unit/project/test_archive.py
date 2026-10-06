from pathlib import Path
from zipfile import ZipFile

import pytest

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

    assert {
        project_file.path: project_file.content
        for project_file in project.files
    } == {
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

    assert {
        project_file.path: project_file.content
        for project_file in loaded.files
    } == {
        project_file.path: project_file.content
        for project_file in project.files
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