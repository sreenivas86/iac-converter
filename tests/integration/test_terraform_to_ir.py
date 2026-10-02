from iac_converter.ir import (
    Literal,
    Reference,
)
from iac_converter.parser.terraform_parser import parse_terraform


def test_terraform_to_ir():

    source = """
terraform {
  required_version = ">= 1.6.0"
}

provider "aws" {
  region = "ap-south-1"
}

resource "aws_s3_bucket" "data" {
  bucket = "company-data"

  tags = {
    Environment = "dev"
    Owner       = "sreenu"
  }
}
"""

    project = parse_terraform(source)

    assert project.version == "1"

    assert len(project.providers) == 1

    provider = project.providers[0]

    assert provider.name == "aws"
    assert provider.configuration["region"] == Literal(
        "ap-south-1"
    )

    assert len(project.resources) == 1

    resource = project.resources[0]

    assert resource.type == "aws_s3_bucket"
    assert resource.name == "data"

    assert resource.attributes["bucket"] == Literal(
        "company-data"
    )

def test_terraform_reference_to_ir():

    source = """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}

resource "aws_s3_bucket_policy" "policy" {
  bucket = aws_s3_bucket.data.id
}
"""

    project = parse_terraform(source)

    policy = project.resources[1]

    bucket = policy.attributes["bucket"]

    assert isinstance(bucket, Reference)

    assert bucket.resource_type == "aws_s3_bucket"
    assert bucket.resource_name == "data"
    assert bucket.attribute == "id"

def test_terraform_expression_to_ir():

    source = """
resource "aws_s3_bucket" "data" {
  count = var.create_bucket ? 1 : 0
}
"""

    project = parse_terraform(source)

    resource = project.resources[0]

    assert resource.count is not None

    assert resource.count.value == (
        "var.create_bucket ? 1 : 0"
    )

def test_terraform_round_trip():

    source = """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
"""

    project1 = parse_terraform(source)

    from iac_converter.generator.terraform import (
        generate_terraform,
    )

    generated = generate_terraform(project1)

    project2 = parse_terraform(generated)

    resource1 = project1.resources[0]
    resource2 = project2.resources[0]

    assert resource1.type == resource2.type
    assert resource1.name == resource2.name
    assert resource1.attributes == resource2.attributes