from iac_converter.compiler.terraform_project import (
    parse_terraform_project_files,
)
from iac_converter.compiler.yaml_project import parse_yaml_project_files
from iac_converter.generator import (
    YAMLProjectGenerationError,
    generate_terraform_project_files,
    generate_yaml_project_files,
)
from iac_converter.project import Project, ProjectFile


def test_generate_terraform_project_preserves_file_paths() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="provider.yaml",
                content="""
version: "1"
providers:
  aws:
    properties:
      region: ap-south-1
""",
            ),
            ProjectFile(
                path="resources/s3.yaml",
                content="""
version: "1"
resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data
""",
            ),
            ProjectFile(
                path="modules/vpc/main.yaml",
                content="""
version: "1"
resources:
  - type: aws_vpc
    name: main
    properties:
      cidr_block: 10.0.0.0/16
""",
            ),
        ]
    )

    parsed_files = parse_yaml_project_files(project)
    result = generate_terraform_project_files(parsed_files)

    files = {item.path: item.content for item in result.files}

    assert set(files) == {
        "provider.tf",
        "resources/s3.tf",
        "modules/vpc/main.tf",
    }

    assert 'provider "aws"' in files["provider.tf"]
    assert 'resource "aws_s3_bucket" "data"' in files["resources/s3.tf"]
    assert 'resource "aws_vpc" "main"' in files["modules/vpc/main.tf"]


def test_generate_terraform_project_files_supports_multiple_blocks() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="main.yaml",
                content="""
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
""",
            ),
        ]
    )

    parsed_files = parse_yaml_project_files(project)
    result = generate_terraform_project_files(parsed_files)

    assert len(result.files) == 1
    assert result.files[0].path == "main.tf"
    assert 'resource "aws_s3_bucket" "data"' in result.files[0].content
    assert 'resource "aws_s3_bucket" "logs"' in result.files[0].content


def test_generate_terraform_project_files_supports_yml_extension() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="resources/network.yml",
                content="""
version: "1"
resources:
  - type: aws_vpc
    name: main
""",
            ),
        ]
    )

    parsed_files = parse_yaml_project_files(project)
    result = generate_terraform_project_files(parsed_files)

    assert result.files[0].path == "resources/network.tf"


def test_generate_terraform_project_files_rejects_empty_input() -> None:
    import pytest

    from iac_converter.generator import TerraformProjectGenerationError

    with pytest.raises(TerraformProjectGenerationError):
        generate_terraform_project_files([])


def test_parse_terraform_project_files_preserves_paths() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="providers.tf",
                content="""
provider "aws" {
  region = "ap-south-1"
}
""",
            ),
            ProjectFile(
                path="resources/s3.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
            ),
            ProjectFile(
                path="modules/vpc/main.tf",
                content="""
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
""",
            ),
        ]
    )

    parsed_files = parse_terraform_project_files(project)

    assert [item.path for item in parsed_files] == [
        "providers.tf",
        "resources/s3.tf",
        "modules/vpc/main.tf",
    ]

    assert len(parsed_files[0].project.providers) == 1
    assert len(parsed_files[1].project.resources) == 1
    assert len(parsed_files[2].project.resources) == 1


def test_parse_terraform_project_files_keeps_files_independent() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="first.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
            ),
            ProjectFile(
                path="second.tf",
                content="""
resource "aws_s3_bucket" "logs" {
  bucket = "company-logs"
}
""",
            ),
        ]
    )

    parsed_files = parse_terraform_project_files(project)

    assert len(parsed_files) == 2
    assert len(parsed_files[0].project.resources) == 1
    assert len(parsed_files[1].project.resources) == 1
    assert parsed_files[0].project.resources[0].name == "data"
    assert parsed_files[1].project.resources[0].name == "logs"


def test_parse_terraform_project_files_ignores_non_terraform_files() -> None:
    project = Project(
        files=[
            ProjectFile(
                path="README.md",
                content="# Terraform project",
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

    parsed_files = parse_terraform_project_files(project)

    assert len(parsed_files) == 1
    assert parsed_files[0].path == "main.tf"


def test_parse_terraform_project_files_rejects_empty_input() -> None:
    import pytest

    from iac_converter.compiler.terraform_project import (
        TerraformProjectParseError,
    )

    with pytest.raises(
        TerraformProjectParseError,
        match="does not contain any Terraform",
    ):
        parse_terraform_project_files(Project(files=[]))


def test_generate_yaml_project_files_preserves_paths() -> None:
    terraform_project = Project(
        files=[
            ProjectFile(
                path="providers.tf",
                content="""
provider "aws" {
  region = "ap-south-1"
}
""",
            ),
            ProjectFile(
                path="resources/s3.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
            ),
            ProjectFile(
                path="modules/vpc/main.tf",
                content="""
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
""",
            ),
        ]
    )

    parsed_files = parse_terraform_project_files(terraform_project)
    result = generate_yaml_project_files(parsed_files)

    files = {item.path: item.content for item in result.files}

    assert set(files) == {
        "providers.yaml",
        "resources/s3.yaml",
        "modules/vpc/main.yaml",
    }

    assert "providers:" in files["providers.yaml"]
    assert "aws_s3_bucket" in files["resources/s3.yaml"]
    assert "aws_vpc" in files["modules/vpc/main.yaml"]


def test_generate_yaml_project_files_keeps_files_independent() -> None:
    terraform_project = Project(
        files=[
            ProjectFile(
                path="first.tf",
                content="""
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
            ),
            ProjectFile(
                path="second.tf",
                content="""
resource "aws_s3_bucket" "logs" {
  bucket = "company-logs"
}
""",
            ),
        ]
    )

    parsed_files = parse_terraform_project_files(terraform_project)
    result = generate_yaml_project_files(parsed_files)

    assert len(result.files) == 2
    assert "company-data" in result.files[0].content
    assert "company-logs" in result.files[1].content


def test_generate_yaml_project_files_ignores_non_terraform_files() -> None:
    from iac_converter.ir import ProjectFileIR, ProjectIR

    parsed_files = [
        ProjectFileIR(path="README.md", project=ProjectIR()),
        ProjectFileIR(path="main.tf", project=ProjectIR()),
    ]

    result = generate_yaml_project_files(parsed_files)

    assert len(result.files) == 1
    assert result.files[0].path == "main.yaml"


def test_generate_yaml_project_files_rejects_empty_input() -> None:
    import pytest

    with pytest.raises(
        YAMLProjectGenerationError,
        match="No YAML files could be generated",
    ):
        generate_yaml_project_files([])


def test_terraform_module_project_preserves_nested_structure() -> None:
    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="""
module "vpc" {
  source      = "./modules/vpc"
  cidr_block  = "10.0.0.0/16"
  environment = "production"
}
""",
            ),
            ProjectFile(
                path="modules/vpc/main.tf",
                content="""
resource "aws_vpc" "main" {
  cidr_block = var.cidr_block
}
""",
            ),
            ProjectFile(
                path="modules/vpc/variables.tf",
                content="""
variable "cidr_block" {
  type = string
}
""",
            ),
        ]
    )

    parsed_files = parse_terraform_project_files(terraform_project)
    result = generate_yaml_project_files(parsed_files)

    files = {item.path: item.content for item in result.files}

    assert set(files) == {
        "main.yaml",
        "modules/vpc/main.yaml",
        "modules/vpc/variables.yaml",
    }

    assert "modules:" in files["main.yaml"]
    assert "name: vpc" in files["main.yaml"]
    assert "source: ./modules/vpc" in files["main.yaml"]
    assert "aws_vpc" in files["modules/vpc/main.yaml"]
    assert "variables:" in files["modules/vpc/variables.yaml"]


def test_yaml_module_project_preserves_nested_structure() -> None:
    yaml_project = Project(
        files=[
            ProjectFile(
                path="main.yaml",
                content="""
version: "1"
modules:
  - name: vpc
    source: ./modules/vpc
    arguments:
      cidr_block: 10.0.0.0/16
      environment: production
""",
            ),
            ProjectFile(
                path="modules/vpc/main.yaml",
                content="""
version: "1"
resources:
  - type: aws_vpc
    name: main
    properties:
      cidr_block:
        expression: var.cidr_block
""",
            ),
            ProjectFile(
                path="modules/vpc/variables.yaml",
                content="""
version: "1"
variables:
  - name: cidr_block
    type: string
""",
            ),
        ]
    )

    parsed_files = parse_yaml_project_files(yaml_project)
    result = generate_terraform_project_files(parsed_files)

    files = {item.path: item.content for item in result.files}

    assert set(files) == {
        "main.tf",
        "modules/vpc/main.tf",
        "modules/vpc/variables.tf",
    }

    assert 'module "vpc"' in files["main.tf"]
    assert 'source = "./modules/vpc"' in files["main.tf"]
    assert 'resource "aws_vpc" "main"' in files["modules/vpc/main.tf"]
    assert 'variable "cidr_block"' in files["modules/vpc/variables.tf"]


def test_terraform_project_files_preserves_module_output_references() -> None:
    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content="""
module "vpc" {
  source = "./modules/vpc"
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
""",
            ),
        ]
    )

    parsed_files = parse_terraform_project_files(terraform_project)
    result = generate_yaml_project_files(parsed_files)

    files = {item.path: item.content for item in result.files}

    assert "main.yaml" in files
    assert "module_reference:" in files["main.yaml"]
    assert "module_name: vpc" in files["main.yaml"]
    assert "output_name: vpc_id" in files["main.yaml"]
