from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.ir import RawExpression, Reference
from iac_converter.project import Project, ProjectFile


def test_resource_meta_arguments_round_trip() -> None:
    yaml_source = """
version: "1"

providers:
  aws:
    properties:
      region: ap-south-1

resources:
  - type: aws_s3_bucket
    name: data
    count:
      expression: var.bucket_count
    properties:
      bucket:
        expression: var.bucket_name

  - type: aws_s3_bucket
    name: logs
    for_each:
      expression: var.buckets
    depends_on:
      - reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
    properties:
      bucket:
        expression: each.value
"""

    # ---------------------------------------------------------
    # YAML -> ProjectIR
    # ---------------------------------------------------------

    original_ir = parse_yaml_project(yaml_source)

    assert len(original_ir.resources) == 2

    original_data = original_ir.resources[0]
    original_logs = original_ir.resources[1]

    assert isinstance(original_data.count, RawExpression)
    assert original_data.count.value == "var.bucket_count"

    assert isinstance(original_logs.for_each, RawExpression)
    assert original_logs.for_each.value == "var.buckets"

    assert len(original_logs.depends_on) == 1
    assert isinstance(original_logs.depends_on[0], Reference)

    # ---------------------------------------------------------
    # ProjectIR -> Terraform
    # ---------------------------------------------------------

    terraform_source = generate_terraform(original_ir)

    assert "count = var.bucket_count" in terraform_source
    assert "for_each = var.buckets" in terraform_source
    assert "depends_on = [aws_s3_bucket.data.id]" in terraform_source
    assert "bucket = var.bucket_name" in terraform_source
    assert "bucket = each.value" in terraform_source

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

    assert len(round_trip_ir.resources) == 2

    round_trip_data = round_trip_ir.resources[0]
    round_trip_logs = round_trip_ir.resources[1]

    # ---------------------------------------------------------
    # count
    # ---------------------------------------------------------

    assert isinstance(round_trip_data.count, RawExpression)
    assert round_trip_data.count.value == "var.bucket_count"

    # ---------------------------------------------------------
    # for_each
    # ---------------------------------------------------------

    assert isinstance(round_trip_logs.for_each, RawExpression)
    assert round_trip_logs.for_each.value == "var.buckets"

    # ---------------------------------------------------------
    # depends_on
    # ---------------------------------------------------------

    assert len(round_trip_logs.depends_on) == 1
    assert isinstance(round_trip_logs.depends_on[0], Reference)

    dependency = round_trip_logs.depends_on[0]

    assert dependency.resource_type == "aws_s3_bucket"
    assert dependency.resource_name == "data"
    assert dependency.attribute == "id"

    # ---------------------------------------------------------
    # Resource attributes
    # ---------------------------------------------------------

    assert isinstance(
        round_trip_data.attributes["bucket"],
        RawExpression,
    )
    assert round_trip_data.attributes["bucket"].value == "var.bucket_name"

    assert isinstance(
        round_trip_logs.attributes["bucket"],
        RawExpression,
    )
    assert round_trip_logs.attributes["bucket"].value == "each.value"
