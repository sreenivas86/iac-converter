import pytest

from iac_converter.compiler import parse_terraform_project_files
from iac_converter.compiler.terraform_project import (
    TerraformProjectParseError,
    parse_terraform_module_project,
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


def test_parse_terraform_module_project_separates_root_and_child_module():
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="""
resource "aws_s3_bucket" "root" {
  bucket = "root-bucket"
}
""",
            ),
            ProjectFile(
                path="modules/vpc/main.tf",
                content="""
variable "cidr_block" {
  type    = string
  default = "10.0.0.0/16"
}

resource "aws_vpc" "main" {
  cidr_block = var.cidr_block
}

output "vpc_id" {
  value = aws_vpc.main.id
}
""",
            ),
        ]
    )

    result = parse_terraform_module_project(project)

    assert len(result.project.resources) == 1
    assert result.project.resources[0].name == "root"

    assert len(result.child_modules) == 1

    vpc = result.child_modules[0]
    assert vpc.path == "modules/vpc"
    assert len(vpc.project.variables) == 1
    assert vpc.project.variables[0].name == "cidr_block"
    assert len(vpc.project.resources) == 1
    assert vpc.project.resources[0].name == "main"
    assert len(vpc.project.outputs) == 1
    assert vpc.project.outputs[0].name == "vpc_id"


def test_parse_terraform_module_project_preserves_module_file_paths():
    project = Project(
        files=[
            ProjectFile(
                path="modules/vpc/main.tf",
                content="""
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
""",
            ),
            ProjectFile(
                path="modules/vpc/outputs.tf",
                content="""
output "vpc_id" {
  value = aws_vpc.main.id
}
""",
            ),
        ]
    )

    result = parse_terraform_module_project(project)

    vpc = result.child_modules[0]

    assert [file.path for file in vpc.files] == ["main.tf", "outputs.tf"]


def test_parse_terraform_module_project_supports_nested_modules():
    project = Project(
        files=[
            ProjectFile(
                path="modules/network/main.tf",
                content="""
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
""",
            ),
            ProjectFile(
                path="modules/network/modules/subnet/main.tf",
                content="""
resource "aws_subnet" "main" {
  vpc_id     = "vpc-123"
  cidr_block = "10.0.1.0/24"
}
""",
            ),
        ]
    )

    result = parse_terraform_module_project(project)

    assert len(result.child_modules) == 1

    network = result.child_modules[0]
    assert network.path == "modules/network"
    assert len(network.project.resources) == 1

    assert len(network.child_modules) == 1

    subnet = network.child_modules[0]
    assert subnet.path == "modules/network/modules/subnet"
    assert len(subnet.project.resources) == 1
    assert subnet.project.resources[0].type == "aws_subnet"


def test_parse_terraform_project_preserves_source_diagnostic():
    from iac_converter.project import Project
    from iac_converter.project.project import ProjectFile

    project = Project(
        files=[
            ProjectFile(
                path="modules/vpc/main.tf",
                content="resource {\n",
            )
        ]
    )

    with pytest.raises(TerraformProjectParseError) as exc_info:
        parse_terraform_project_files(project)

    diagnostic = exc_info.value.__cause__.diagnostic

    assert diagnostic.code == "TF001"
    assert diagnostic.file_path == "modules/vpc/main.tf"
    assert diagnostic.line == 2
    assert diagnostic.column == 1


def test_terraform_project_merge_preserves_import_diagnostics():
    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content='resource "aws_s3_bucket" "example" {\n  bucket = "example"\n}\n',
            ),
            ProjectFile(
                path="modules/storage/import.tf",
                content=(
                    'import {\n  to = aws_s3_bucket.example\n  id = "existing-bucket-id"\n}\n'
                ),
            ),
        ]
    )

    parsed = parse_terraform_project(project)

    assert len(parsed.diagnostics) == 1

    diagnostic = parsed.diagnostics[0]

    assert diagnostic.code == "TF002"
    assert diagnostic.file_path == "modules/storage/import.tf"
