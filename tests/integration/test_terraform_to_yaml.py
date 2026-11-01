from iac_converter.compiler.terraform_project import parse_terraform_project
from iac_converter.generator.terraform import generate_terraform
from iac_converter.generator.yaml import generate_yaml
from iac_converter.ir import (
    CollectionExpression,
    RawExpression,
    Reference,
)
from iac_converter.parser.terraform_parser import parse_terraform
from iac_converter.parser.yaml_parser import parse_yaml
from iac_converter.project import Project, ProjectFile


def test_terraform_to_yaml():

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

    result = generate_yaml(project)

    assert 'version: "1"' in result
    assert "providers:" in result
    assert "aws:" in result
    assert "resources:" in result
    assert "aws_s3_bucket" in result
    assert "company-data" in result


def test_reference_preservation():

    source = """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}

resource "aws_s3_bucket_policy" "policy" {
  bucket = aws_s3_bucket.data.id
}
"""

    project = parse_terraform(source)

    result = generate_yaml(project)

    assert "reference:" in result
    assert "resource_type: aws_s3_bucket" in result
    assert "resource_name: data" in result
    assert "attribute: id" in result


def test_expression_preservation():

    source = """
resource "aws_s3_bucket" "data" {
  count = var.create_bucket ? 1 : 0
}
"""

    project = parse_terraform(source)

    result = generate_yaml(project)

    assert "expression:" in result
    assert "var.create_bucket ? 1 : 0" in result


def test_full_round_trip():

    yaml_source = """
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

  - type: aws_s3_bucket_policy
    name: policy
    properties:
      bucket:
        reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
"""

    # YAML -> IR
    project1 = parse_yaml(yaml_source)

    # IR -> Terraform
    terraform = generate_terraform(project1)

    # Terraform -> IR
    project2 = parse_terraform(terraform)

    # IR -> YAML
    yaml_result = generate_yaml(project2)

    # Parse generated YAML again.
    project3 = parse_yaml(yaml_result)

    assert len(project3.resources) == 2

    data_bucket = project3.resources[0]

    assert data_bucket.type == "aws_s3_bucket"
    assert data_bucket.name == "data"

    policy = project3.resources[1]

    assert policy.type == "aws_s3_bucket_policy"
    assert policy.name == "policy"


def test_nested_map_preserves_reference_and_function_call():
    source = """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}

output "settings" {
  value = {
    bucket_id       = aws_s3_bucket.data.id
    normalized_name = lower("MY-BUCKET")
  }
}
"""

    project = parse_terraform(source)
    result = generate_yaml(project)

    # The reference should use the explicit YAML reference representation.
    assert "reference:" in result
    assert "resource_type: aws_s3_bucket" in result
    assert "resource_name: data" in result
    assert "attribute: id" in result

    # The function call should use the explicit expression representation.
    assert "expression:" in result
    assert 'lower("MY-BUCKET")' in result
    reparsed_project = parse_yaml(result)
    reparsed_value = reparsed_project.outputs[0].value

    assert isinstance(reparsed_value, CollectionExpression)
    assert reparsed_value.kind == "map"

    values = dict(reparsed_value.items)

    reference = values["bucket_id"]
    assert isinstance(reference, Reference)
    assert reference.to_string() == "aws_s3_bucket.data.id"

    function = values["normalized_name"]
    assert isinstance(function, RawExpression)
    assert function.value == 'lower("MY-BUCKET")'


def test_terraform_module_to_yaml():
    source = """
module "vpc" {
  source      = "./modules/vpc"
  cidr_block  = "10.0.0.0/16"
  environment = "production"
}
"""

    project = parse_terraform(source)
    result = generate_yaml(project)

    assert "modules:" in result
    assert "name: vpc" in result
    assert "source: ./modules/vpc" in result
    assert "cidr_block: 10.0.0.0/16" in result
    assert "environment: production" in result


def test_terraform_module_yaml_round_trip():
    source = """
module "vpc" {
  source      = "./modules/vpc"
  cidr_block  = "10.0.0.0/16"
  environment = "production"
}
"""

    project1 = parse_terraform(source)
    yaml_result = generate_yaml(project1)
    project2 = parse_yaml(yaml_result)

    assert len(project2.modules) == 1

    module = project2.modules[0]

    assert module.name == "vpc"
    assert module.source == "./modules/vpc"
    assert module.arguments["cidr_block"].value == "10.0.0.0/16"
    assert module.arguments["environment"].value == "production"


def test_terraform_project_merge_preserves_modules():
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="""
module "vpc" {
  source = "./modules/vpc"
}
""",
            ),
            ProjectFile(
                path="modules/network.tf",
                content="""
module "network" {
  source = "./modules/network"
}
""",
            ),
        ]
    )

    merged = parse_terraform_project(project)

    assert len(merged.modules) == 2
    assert merged.modules[0].name == "vpc"
    assert merged.modules[0].source == "./modules/vpc"
    assert merged.modules[1].name == "network"
    assert merged.modules[1].source == "./modules/network"
