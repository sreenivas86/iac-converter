from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.generator.yaml import generate_yaml
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

    assert round_trip_variable.description == original_variable.description

    assert round_trip_variable.default == original_variable.default

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

    assert round_trip_resource.attributes["bucket"] == original_resource.attributes["bucket"]

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
    # ---------------------------------------------------------
    # Terraform IR -> YAML -> ProjectIR
    # ---------------------------------------------------------

    yaml_after_round_trip = generate_yaml(round_trip_ir)
    yaml_reparsed_ir = parse_yaml_project(yaml_after_round_trip)

    assert yaml_reparsed_ir.version == original_ir.version

    assert len(yaml_reparsed_ir.providers) == len(original_ir.providers)
    assert len(yaml_reparsed_ir.variables) == len(original_ir.variables)
    assert len(yaml_reparsed_ir.resources) == len(original_ir.resources)
    assert len(yaml_reparsed_ir.outputs) == len(original_ir.outputs)

    # Provider
    assert yaml_reparsed_ir.providers[0].name == original_ir.providers[0].name
    assert (
        yaml_reparsed_ir.providers[0].configuration["region"]
        == original_ir.providers[0].configuration["region"]
    )

    # Variable
    assert yaml_reparsed_ir.variables[0].name == original_ir.variables[0].name
    assert yaml_reparsed_ir.variables[0].description == original_ir.variables[0].description
    assert yaml_reparsed_ir.variables[0].default == original_ir.variables[0].default

    # Resource
    assert yaml_reparsed_ir.resources[0].type == original_ir.resources[0].type
    assert yaml_reparsed_ir.resources[0].name == original_ir.resources[0].name
    assert (
        yaml_reparsed_ir.resources[0].attributes["bucket"]
        == original_ir.resources[0].attributes["bucket"]
    )
    assert (
        yaml_reparsed_ir.resources[0].attributes["tags"]
        == original_ir.resources[0].attributes["tags"]
    )

    # Output
    assert yaml_reparsed_ir.outputs[0].name == original_ir.outputs[0].name
    assert yaml_reparsed_ir.outputs[0].value == original_ir.outputs[0].value


def test_nested_expressions_survive_yaml_terraform_round_trip() -> None:

    from iac_converter.ir import (
        CollectionExpression,
        Literal,
        RawExpression,
        Reference,
    )

    yaml_source = """
resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data

outputs:
  - name: settings
    value:
      bucket_id:
        reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
      normalized_name:
        expression: lower("MY-BUCKET")
      nested:
        regions:
          - ap-south-1
          - ap-southeast-1
"""

    original_ir = parse_yaml_project(yaml_source)
    terraform_source = generate_terraform(original_ir)

    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content=terraform_source,
            )
        ]
    )

    round_trip_ir = parse_terraform_project(terraform_project)

    assert len(round_trip_ir.outputs) == 1
    output = round_trip_ir.outputs[0]
    assert output.name == "settings"

    value = output.value
    assert isinstance(value, dict)

    values = value

    # Resource reference remains typed.
    reference = values["bucket_id"]
    assert isinstance(reference, Reference)
    assert reference.to_string() == "aws_s3_bucket.data.id"

    # Function expression remains represented as raw Terraform syntax.
    function = values["normalized_name"]
    assert isinstance(function, RawExpression)
    assert function.value == 'lower("MY-BUCKET")'

    # Nested map and list retain their values.
    nested = values["nested"]
    assert isinstance(nested, dict)

    regions = nested["regions"]
    assert isinstance(regions, list)
    assert regions == [
        Literal("ap-south-1"),
        Literal("ap-southeast-1"),
    ]
    # Terraform IR -> YAML -> IR
    yaml_after_round_trip = generate_yaml(round_trip_ir)
    yaml_reparsed_ir = parse_yaml_project(yaml_after_round_trip)

    assert len(yaml_reparsed_ir.outputs) == 1

    reparsed_value = yaml_reparsed_ir.outputs[0].value
    assert isinstance(reparsed_value, CollectionExpression)
    assert reparsed_value.kind == "map"

    reparsed_items = dict(reparsed_value.items)

    # Resource reference remains typed.
    reparsed_reference = reparsed_items["bucket_id"]
    assert isinstance(reparsed_reference, Reference)
    assert reparsed_reference.to_string() == "aws_s3_bucket.data.id"

    # Function expression remains represented in the IR.
    reparsed_function = reparsed_items["normalized_name"]
    assert isinstance(reparsed_function, RawExpression)
    assert reparsed_function.value == 'lower("MY-BUCKET")'

    # Nested map and list remain represented as collections.
    reparsed_nested = reparsed_items["nested"]
    assert isinstance(reparsed_nested, CollectionExpression)
    assert reparsed_nested.kind == "map"

    nested_items = dict(reparsed_nested.items)
    reparsed_regions = nested_items["regions"]

    assert isinstance(reparsed_regions, CollectionExpression)
    assert reparsed_regions.kind == "list"
    assert reparsed_regions.items == (
        Literal("ap-south-1"),
        Literal("ap-southeast-1"),
    )
