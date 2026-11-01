import pytest

from iac_converter.compiler.yaml_project import (
    YAMLProjectParseError,
    parse_yaml_project_files,
)
from iac_converter.project import Project, ProjectFile


def test_parse_multiple_yaml_project_files() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="provider.yaml",
                content="""
version: "1"
providers:
  aws:
    properties:
      region: ap-south-1
""",
            ),
            ProjectFile(
                path="resources/s3.yaml",
                content="""
version: "1"
resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data
""",
            ),
        ]
    )

    result = parse_yaml_project_files(project)

    assert len(result) == 2

    assert result[0].path == "provider.yaml"
    assert len(result[0].project.providers) == 1
    assert result[0].project.providers[0].name == "aws"

    assert result[1].path == "resources/s3.yaml"
    assert len(result[1].project.resources) == 1
    assert result[1].project.resources[0].name == "data"


def test_parse_yaml_project_files_preserves_nested_paths() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="modules/networking/resources/vpc.yaml",
                content="""
version: "1"
resources:
  - type: aws_vpc
    name: main
""",
            ),
        ]
    )

    result = parse_yaml_project_files(project)

    assert result[0].path == "modules/networking/resources/vpc.yaml"


def test_parse_yaml_project_files_ignores_non_yaml_files() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="README.md",
                content="# Project",
            ),
            ProjectFile(
                path="resources/s3.yaml",
                content="""
version: "1"
resources:
  - type: aws_s3_bucket
    name: data
""",
            ),
        ]
    )

    result = parse_yaml_project_files(project)

    assert len(result) == 1
    assert result[0].path == "resources/s3.yaml"


def test_parse_yaml_project_files_reports_invalid_file_path() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="resources/invalid.yaml",
                content="""
version: "1"
resources:
  - type: aws_s3_bucket
    name: data
    unexpected: true
""",
            ),
        ]
    )

    with pytest.raises(
        YAMLProjectParseError,
        match="resources/invalid.yaml",
    ):
        parse_yaml_project_files(project)


def test_parse_yaml_project_files_rejects_empty_yaml_project() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="README.md",
                content="# No YAML files",
            ),
        ]
    )

    with pytest.raises(YAMLProjectParseError, match="No YAML files"):
        parse_yaml_project_files(project)
