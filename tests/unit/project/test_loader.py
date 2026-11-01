from pathlib import Path

import pytest

from iac_converter.project import (
    ProjectLoadError,
    load_project,
)


def test_load_project_reads_files_recursively(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text(
        'resource "aws_s3_bucket" "data" {}\n',
        encoding="utf-8",
    )

    (tmp_path / "variables.tf").write_text(
        'variable "bucket_name" {}\n',
        encoding="utf-8",
    )

    nested = tmp_path / "modules" / "storage"
    nested.mkdir(parents=True)

    (nested / "bucket.tf").write_text(
        'resource "aws_s3_bucket" "nested" {}\n',
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "# Example project\n",
        encoding="utf-8",
    )

    project = load_project(tmp_path)

    assert [project_file.path for project_file in project.files] == [
        "README.md",
        "main.tf",
        "modules/storage/bucket.tf",
        "variables.tf",
    ]


def test_load_project_preserves_file_content(tmp_path: Path) -> None:
    content = """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""".strip()

    (tmp_path / "main.tf").write_text(
        content,
        encoding="utf-8",
    )

    project = load_project(tmp_path)

    assert len(project.files) == 1
    assert project.files[0].path == "main.tf"
    assert project.files[0].content == content


def test_load_project_handles_empty_directory(tmp_path: Path) -> None:
    project = load_project(tmp_path)

    assert project.files == []


def test_load_project_rejects_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    with pytest.raises(ProjectLoadError, match="does not exist"):
        load_project(missing)


def test_load_project_rejects_file_path(tmp_path: Path) -> None:
    file_path = tmp_path / "main.tf"

    file_path.write_text(
        'resource "aws_s3_bucket" "data" {}\n',
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError, match="not a directory"):
        load_project(file_path)


def test_load_project_accepts_string_path(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text(
        'resource "aws_s3_bucket" "data" {}\n',
        encoding="utf-8",
    )

    project = load_project(str(tmp_path))

    assert len(project.files) == 1
    assert project.files[0].path == "main.tf"


def test_load_project_normalizes_nested_paths(tmp_path: Path) -> None:
    nested = tmp_path / "modules" / "storage"
    nested.mkdir(parents=True)

    (nested / "main.tf").write_text(
        'resource "aws_s3_bucket" "data" {}\n',
        encoding="utf-8",
    )

    project = load_project(tmp_path)

    assert project.files[0].path == "modules/storage/main.tf"
