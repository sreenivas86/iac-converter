from iac_converter.compiler.terraform_project import (
    TerraformProjectParseError,
    parse_terraform_project,
)
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