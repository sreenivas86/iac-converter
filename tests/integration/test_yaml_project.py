
import pytest

from iac_converter.compiler import (
    YAMLProjectParseError,
    parse_yaml_project,
)
from iac_converter.ir import (
    Literal,
    RawExpression,
    Reference,
)


def test_parse_yaml_project() -> None:
    source = """
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

outputs:
  - name: bucket_id
    value:
      reference:
        resource_type: aws_s3_bucket
        resource_name: data
        attribute: id
"""

    result = parse_yaml_project(source)

    assert result.version == "1"

    assert result.terraform["required_version"] == ">= 1.6.0"

    assert len(result.providers) == 1
    assert result.providers[0].name == "aws"
    assert result.providers[0].configuration["region"] == "ap-south-1"

    assert len(result.variables) == 1
    assert result.variables[0].name == "bucket_name"
    assert result.variables[0].default == Literal(
        "company-data"
    )

    assert len(result.resources) == 1

    resource = result.resources[0]

    assert resource.type == "aws_s3_bucket"
    assert resource.name == "data"

    assert resource.attributes["bucket"] == RawExpression(
        "var.bucket_name"
    )

    assert len(result.outputs) == 1

    output = result.outputs[0]

    assert output.name == "bucket_id"
    assert output.value == Reference(
        resource_type="aws_s3_bucket",
        resource_name="data",
        attribute="id",
    )


def test_parse_yaml_project_supports_multiple_resources() -> None:
    source = """
version: "1"

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data

  - type: aws_s3_bucket
    name: logs
    properties:
      bucket: company-logs
"""

    result = parse_yaml_project(source)

    assert len(result.resources) == 2

    assert result.resources[0].type == "aws_s3_bucket"
    assert result.resources[0].name == "data"

    assert result.resources[1].type == "aws_s3_bucket"
    assert result.resources[1].name == "logs"


def test_parse_yaml_project_supports_expression_and_reference() -> None:
    source = """
version: "1"

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket:
        expression: var.bucket_name
      source:
        reference:
          resource_type: aws_s3_bucket
          resource_name: source
          attribute: id
"""

    result = parse_yaml_project(source)

    resource = result.resources[0]

    assert resource.attributes["bucket"] == RawExpression(
        "var.bucket_name"
    )

    assert resource.attributes["source"] == Reference(
        resource_type="aws_s3_bucket",
        resource_name="source",
        attribute="id",
    )


def test_parse_yaml_project_rejects_invalid_yaml() -> None:
    source = """
version: "1"

resources:
  - type: aws_s3_bucket
    name: data
    unexpected: true
"""

    with pytest.raises(YAMLProjectParseError):
        parse_yaml_project(source)
