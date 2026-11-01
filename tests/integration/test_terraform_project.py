from iac_converter.compiler.terraform_project import (
    TerraformProjectParseError,
    parse_terraform_project,
)
from iac_converter.ir import Literal
from iac_converter.project import Project, ProjectFile


def test_parse_terraform_project_merges_multiple_files():
    project = Project(
        files=[
            ProjectFile(
                path="providers.tf",
                content="""
terraform {
  required_version = ">= 1.6.0"
}

provider "aws" {
  region = "ap-south-1"
}
""",
            ),
            ProjectFile(
                path="variables.tf",
                content="""
variable "bucket_name" {
  type        = string
  description = "Name of the bucket"
  default     = "company-data"
}
""",
            ),
            ProjectFile(
                path="main.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name

  tags = {
    Environment = "dev"
  }
}
""",
            ),
            ProjectFile(
                path="outputs.tf",
                content="""
output "bucket_id" {
  value = aws_s3_bucket.data.id
}
""",
            ),
        ]
    )

    result = parse_terraform_project(project)

    assert result.terraform["required_version"].value == ">= 1.6.0"

    assert len(result.providers) == 1
    assert result.providers[0].name == "aws"
    assert result.providers[0].configuration["region"].value == "ap-south-1"

    assert len(result.variables) == 1
    assert result.variables[0].name == "bucket_name"

    assert len(result.resources) == 1
    assert result.resources[0].type == "aws_s3_bucket"
    assert result.resources[0].name == "data"

    assert len(result.outputs) == 1
    assert result.outputs[0].name == "bucket_id"


def test_parse_terraform_project_ignores_non_terraform_files():
    project = Project(
        files=[
            ProjectFile(
                path="README.md",
                content="# My Terraform project",
            ),
            ProjectFile(
                path="terraform.tfvars",
                content='bucket_name = "company-data"',
            ),
            ProjectFile(
                path="main.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
            ),
        ]
    )

    result = parse_terraform_project(project)

    assert len(result.resources) == 1
    assert result.resources[0].type == "aws_s3_bucket"
    assert result.resources[0].name == "data"


def test_parse_terraform_project_requires_terraform_files():
    project = Project(
        files=[
            ProjectFile(
                path="README.md",
                content="# Empty Terraform project",
            ),
        ]
    )

    try:
        parse_terraform_project(project)
    except TerraformProjectParseError as exc:
        assert "Terraform (.tf)" in str(exc)
    else:
        raise AssertionError("Expected TerraformProjectParseError")


def test_parse_terraform_project_accepts_nested_terraform_paths():
    project = Project(
        files=[
            ProjectFile(
                path="modules/storage/main.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
            ),
            ProjectFile(
                path="environments/dev/main.tf",
                content="""
resource "aws_s3_bucket" "logs" {
  bucket = "company-logs"
}
""",
            ),
        ]
    )

    result = parse_terraform_project(project)

    assert len(result.resources) == 2
    assert result.resources[0].name == "data"
    assert result.resources[1].name == "logs"


def test_parse_terraform_project_preserves_nested_output_expressions():
    from iac_converter.ir import RawExpression, Reference

    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}

output "settings" {
  value = {
    bucket_id = aws_s3_bucket.data.id
    normalized_name = lower("MY-BUCKET")
    nested = {
      regions = ["ap-south-1", "ap-southeast-1"]
    }
  }
}
""",
            ),
        ]
    )

    result = parse_terraform_project(project)

    settings = result.outputs[0].value

    assert isinstance(settings, dict)
    assert isinstance(settings["bucket_id"], Reference)
    assert settings["bucket_id"].resource_name == "data"
    assert isinstance(settings["normalized_name"], RawExpression)
    assert settings["normalized_name"].value == 'lower("MY-BUCKET")'
    assert settings["nested"]["regions"] == [
        Literal("ap-south-1"),
        Literal("ap-southeast-1"),
    ]
