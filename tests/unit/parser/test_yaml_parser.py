from iac_converter.ir import Literal, ProjectIR, Reference
from iac_converter.parser.yaml_parser import parse_yaml


def test_parse_s3_bucket():

    source = """
version: "1"

terraform:
  required_version: ">= 1.6.0"

providers:
  aws:
    properties:
      region: ap-south-1

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data
      tags:
        Environment: dev
        Owner: sreenu
"""

    project = parse_yaml(source)

    assert isinstance(project, ProjectIR)

    assert project.version == "1"

    assert len(project.providers) == 1
    assert project.providers[0].name == "aws"

    assert len(project.resources) == 1

    resource = project.resources[0]

    assert resource.type == "aws_s3_bucket"
    assert resource.name == "data"

    assert resource.attributes["bucket"] == Literal("company-data")

def test_parse_reference():

    source = """
resources:
  - type: aws_s3_bucket
    name: backup
    properties:
      bucket:
        reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
"""

    project = parse_yaml(source)

    value = project.resources[0].attributes["bucket"]

    assert isinstance(value, Reference)

    assert value.to_string() == "aws_s3_bucket.data.id"