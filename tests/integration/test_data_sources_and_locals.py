from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.project import Project, ProjectFile


def test_yaml_data_sources_and_locals_to_terraform_to_ir() -> None:
    yaml_source = """
version: "1"

providers:
  aws:
    properties:
      region: ap-south-1

locals:
  environment: dev
  bucket_prefix: company

data_sources:
  - type: aws_caller_identity
    name: current

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket:
        expression: local.bucket_prefix
      tags:
        Environment:
          expression: local.environment
"""

    # YAML -> ProjectIR
    original_ir = parse_yaml_project(yaml_source)

    # ProjectIR -> Terraform
    terraform_source = generate_terraform(original_ir)

    # Terraform -> Project
    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content=terraform_source,
            )
        ]
    )

    # Project -> ProjectIR
    round_trip_ir = parse_terraform_project(terraform_project)

    # ---------------------------------------------------------
    # Locals
    # ---------------------------------------------------------

    assert "environment" in round_trip_ir.locals
    assert "bucket_prefix" in round_trip_ir.locals

    assert round_trip_ir.locals["environment"].value == original_ir.locals["environment"]

    assert round_trip_ir.locals["bucket_prefix"].value == original_ir.locals["bucket_prefix"]

    # ---------------------------------------------------------
    # Data sources
    # ---------------------------------------------------------

    assert len(round_trip_ir.data_sources) == 1

    round_trip_data_source = round_trip_ir.data_sources[0]
    original_data_source = original_ir.data_sources[0]

    assert round_trip_data_source.type == original_data_source.type
    assert round_trip_data_source.name == original_data_source.name

    # ---------------------------------------------------------
    # Resource
    # ---------------------------------------------------------

    assert len(round_trip_ir.resources) == 1

    round_trip_resource = round_trip_ir.resources[0]
    original_resource = original_ir.resources[0]

    assert round_trip_resource.type == original_resource.type
    assert round_trip_resource.name == original_resource.name

    assert round_trip_resource.attributes["bucket"] == original_resource.attributes["bucket"]

    assert (
        round_trip_resource.attributes["tags"]["Environment"]
        == original_resource.attributes["tags"]["Environment"]
    )
