from pathlib import Path

import pytest

from iac_converter.project import (
    Project,
    ProjectFile,
    ProjectWriteError,
    load_project,
    save_project,
)


def test_save_project_writes_files(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content='resource "aws_s3_bucket" "data" {}\n',
            ),
            ProjectFile(
                path="variables.tf",
                content='variable "bucket_name" {}\n',
            ),
        ]
    )

    output = tmp_path / "output"

    save_project(project, output)

    assert (output / "main.tf").read_text(encoding="utf-8") == (
        'resource "aws_s3_bucket" "data" {}\n'
    )

    assert (output / "variables.tf").read_text(encoding="utf-8") == (
        'variable "bucket_name" {}\n'
    )


def test_save_project_creates_nested_directories(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="modules/storage/main.tf",
                content='resource "aws_s3_bucket" "data" {}\n',
            ),
        ]
    )

    output = tmp_path / "output"

    save_project(project, output)

    assert (
        output / "modules" / "storage" / "main.tf"
    ).read_text(encoding="utf-8") == (
        'resource "aws_s3_bucket" "data" {}\n'
    )


def test_save_project_creates_output_directory(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="# Terraform\n",
            ),
        ]
    )

    output = tmp_path / "does-not-exist" / "project"

    save_project(project, output)

    assert output.is_dir()
    assert (output / "main.tf").exists()


def test_save_project_preserves_utf8_content(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="README.md",
                content="# S3 配置 — café\n",
            ),
        ]
    )

    output = tmp_path / "output"

    save_project(project, output)

    assert (output / "README.md").read_text(encoding="utf-8") == (
        "# S3 配置 — café\n"
    )


def test_save_project_accepts_windows_style_relative_paths(
    tmp_path: Path,
) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="modules\\storage\\main.tf",
                content="# Terraform\n",
            ),
        ]
    )

    output = tmp_path / "output"

    save_project(project, output)

    assert (
        output / "modules" / "storage" / "main.tf"
    ).read_text(encoding="utf-8") == "# Terraform\n"


def test_save_project_rejects_absolute_path(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path=str(tmp_path / "outside.tf"),
                content="# Must not be written\n",
            ),
        ]
    )

    output = tmp_path / "output"

    with pytest.raises(ProjectWriteError, match="must be relative"):
        save_project(project, output)


def test_save_project_rejects_parent_directory_escape(
    tmp_path: Path,
) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="../outside.tf",
                content="# Must not be written\n",
            ),
        ]
    )

    output = tmp_path / "output"

    with pytest.raises(
        ProjectWriteError,
        match="escapes project directory",
    ):
        save_project(project, output)

    assert not (tmp_path / "outside.tf").exists()


def test_save_project_rejects_duplicate_paths(
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

    output = tmp_path / "output"

    with pytest.raises(
        ProjectWriteError,
        match="Duplicate project file path",
    ):
        save_project(project, output)


def test_save_project_round_trip(tmp_path: Path) -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content='resource "aws_s3_bucket" "data" {}\n',
            ),
            ProjectFile(
                path="variables.tf",
                content='variable "bucket_name" {}\n',
            ),
            ProjectFile(
                path="modules/storage/main.tf",
                content="# Nested Terraform\n",
            ),
            ProjectFile(
                path="README.md",
                content="# Example project\n",
            ),
        ]
    )

    output = tmp_path / "output"

    save_project(project, output)

    loaded = load_project(output)

    assert {
        project_file.path: project_file.content
        for project_file in loaded.files
    } == {
        project_file.path: project_file.content
        for project_file in project.files
    }