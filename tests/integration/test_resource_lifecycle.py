
from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.ir import Literal
from iac_converter.project import Project, ProjectFile


def test_resource_lifecycle_round_trip() -> None:
    yaml_source = """
version: "1"

providers:
  aws:
    properties:
      region: ap-south-1

resources:
  - type: aws_s3_bucket
    name: data
    lifecycle:
      prevent_destroy: true
      create_before_destroy: true
      ignore_changes:
        - tags
        - bucket
    properties:
      bucket: company-data
"""

    # ---------------------------------------------------------
    # YAML -> ProjectIR
    # ---------------------------------------------------------

    original_ir = parse_yaml_project(yaml_source)

    assert len(original_ir.resources) == 1

    original_resource = original_ir.resources[0]

    assert (
        original_resource.lifecycle["prevent_destroy"]
        == Literal(True)
    )

    assert (
        original_resource.lifecycle["create_before_destroy"]
        == Literal(True)
    )

    assert original_resource.lifecycle["ignore_changes"] == [
        Literal("tags"),
        Literal("bucket"),
    ]

    # ---------------------------------------------------------
    # ProjectIR -> Terraform
    # ---------------------------------------------------------

    terraform_source = generate_terraform(original_ir)

    assert "lifecycle {" in terraform_source
    assert "prevent_destroy = true" in terraform_source
    assert "create_before_destroy = true" in terraform_source
    assert "ignore_changes = [tags, bucket]" in terraform_source

    # ---------------------------------------------------------
    # Terraform -> Project
    # ---------------------------------------------------------

    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content=terraform_source,
            )
        ]
    )

    # ---------------------------------------------------------
    # Project -> ProjectIR
    # ---------------------------------------------------------

    round_trip_ir = parse_terraform_project(terraform_project)

    assert len(round_trip_ir.resources) == 1

    round_trip_resource = round_trip_ir.resources[0]

    # Lifecycle booleans
    assert (
        round_trip_resource.lifecycle["prevent_destroy"]
        == Literal(True)
    )

    assert (
        round_trip_resource.lifecycle["create_before_destroy"]
        == Literal(True)
    )

    # ignore_changes
    assert round_trip_resource.lifecycle["ignore_changes"] == [
        Literal("tags"),
        Literal("bucket"),
    ]
