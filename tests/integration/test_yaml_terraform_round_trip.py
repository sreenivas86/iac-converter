
from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.project import Project, ProjectFile


def test_yaml_to_terraform_to_ir_round_trip() -> None:
    yaml_source = """
version: "1"

terraform:
  required_version: ">= 1.6.0"

providers:
  aws:
    properties:
      region: ap-south-1

variables:
  - name: bucket_name
    description: S3 bucket name
    default: company-data

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket:
        expression: var.bucket_name
      tags:
        Environment: dev
        Owner: sreenu

outputs:
  - name: bucket_id
    value:
      reference:
        resource_type: aws_s3_bucket
        resource_name: data
        attribute: id
"""

    # ---------------------------------------------------------
    # YAML -> ProjectIR
    # ---------------------------------------------------------

    original_ir = parse_yaml_project(yaml_source)

    # ---------------------------------------------------------
    # ProjectIR -> Terraform
    # ---------------------------------------------------------

    terraform_source = generate_terraform(original_ir)

    # ---------------------------------------------------------
    # Terraform text -> Project
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

    # ---------------------------------------------------------
    # Project version
    # ---------------------------------------------------------

    assert round_trip_ir.version == original_ir.version

    # ---------------------------------------------------------
    # Terraform configuration
    #
    # YAML parser stores required_version as a plain string.
    # Terraform parser stores scalar HCL values as Literal.
    # Compare their semantic values.
    # ---------------------------------------------------------

    assert (
        round_trip_ir.terraform["required_version"].value
        == original_ir.terraform["required_version"]
    )

    # ---------------------------------------------------------
    # Provider
    #
    # YAML parser stores provider scalar configuration values
    # as plain values.
    # Terraform parser stores them as Literal.
    # ---------------------------------------------------------

    assert len(round_trip_ir.providers) == len(original_ir.providers)

    round_trip_provider = round_trip_ir.providers[0]
    original_provider = original_ir.providers[0]

    assert round_trip_provider.name == original_provider.name
    assert round_trip_provider.alias == original_provider.alias

    assert (
        round_trip_provider.configuration["region"].value
        == original_provider.configuration["region"]
    )

    # ---------------------------------------------------------
    # Variable
    # ---------------------------------------------------------

    assert len(round_trip_ir.variables) == len(original_ir.variables)

    round_trip_variable = round_trip_ir.variables[0]
    original_variable = original_ir.variables[0]

    assert round_trip_variable.name == original_variable.name

    assert (
        round_trip_variable.description
        == original_variable.description
    )

    assert (
        round_trip_variable.default
        == original_variable.default
    )

    # ---------------------------------------------------------
    # Resource
    # ---------------------------------------------------------

    assert len(round_trip_ir.resources) == len(original_ir.resources)

    round_trip_resource = round_trip_ir.resources[0]
    original_resource = original_ir.resources[0]

    assert round_trip_resource.type == original_resource.type
    assert round_trip_resource.name == original_resource.name

    # ---------------------------------------------------------
    # Resource expression
    #
    # YAML:
    #
    # bucket:
    #   expression: var.bucket_name
    #
    # Terraform:
    #
    # bucket = var.bucket_name
    # ---------------------------------------------------------

    assert (
        round_trip_resource.attributes["bucket"]
        == original_resource.attributes["bucket"]
    )

    # ---------------------------------------------------------
    # Resource nested map
    # ---------------------------------------------------------

    assert (
        round_trip_resource.attributes["tags"]["Environment"]
        == original_resource.attributes["tags"]["Environment"]
    )

    assert (
        round_trip_resource.attributes["tags"]["Owner"]
        == original_resource.attributes["tags"]["Owner"]
    )

    # ---------------------------------------------------------
    # Output
    #
    # The output value is a Reference on both sides.
    # ---------------------------------------------------------

    assert len(round_trip_ir.outputs) == len(original_ir.outputs)

    round_trip_output = round_trip_ir.outputs[0]
    original_output = original_ir.outputs[0]

    assert round_trip_output.name == original_output.name
    assert round_trip_output.value == original_output.value
