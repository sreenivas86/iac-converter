from iac_converter.generator import generate_terraform_project
from iac_converter.ir import (
    Literal,
    Output,
    ProjectIR,
    Provider,
    Reference,
    Resource,
    Variable,
)


def test_generate_terraform_project_creates_expected_files() -> None:
    project = ProjectIR(
        terraform={
            "required_version": Literal(">= 1.6.0"),
        },
        providers=[
            Provider(
                name="aws",
                configuration={
                    "region": Literal("ap-south-1"),
                },
            )
        ],
        variables=[
            Variable(
                name="bucket_name",
                description="S3 bucket name",
                default=Literal("company-data"),
            )
        ],
        resources=[
            Resource(
                type="aws_s3_bucket",
                name="data",
                attributes={
                    "bucket": Literal("company-data"),
                },
            )
        ],
        outputs=[
            Output(
                name="bucket_id",
                value=Reference(
                    resource_type="aws_s3_bucket",
                    resource_name="data",
                    attribute="id",
                ),
            )
        ],
    )

    result = generate_terraform_project(project)

    assert [project_file.path for project_file in result.files] == [
        "terraform.tf",
        "providers.tf",
        "variables.tf",
        "main.tf",
        "outputs.tf",
    ]

    contents = {
        project_file.path: project_file.content
        for project_file in result.files
    }

    assert 'terraform {' in contents["terraform.tf"]
    assert 'required_version = ">= 1.6.0"' in contents["terraform.tf"]

    assert 'provider "aws" {' in contents["providers.tf"]
    assert 'region = "ap-south-1"' in contents["providers.tf"]

    assert 'variable "bucket_name" {' in contents["variables.tf"]
    assert 'default = "company-data"' in contents["variables.tf"]

    assert 'resource "aws_s3_bucket" "data" {' in contents["main.tf"]
    assert 'bucket = "company-data"' in contents["main.tf"]

    assert 'output "bucket_id" {' in contents["outputs.tf"]
    assert "value = aws_s3_bucket.data.id" in contents["outputs.tf"]


def test_generate_terraform_project_omits_empty_files() -> None:
    project = ProjectIR(
        resources=[
            Resource(
                type="aws_s3_bucket",
                name="data",
                attributes={
                    "bucket": Literal("company-data"),
                },
            )
        ]
    )

    result = generate_terraform_project(project)

    assert [project_file.path for project_file in result.files] == [
        "main.tf",
    ]


def test_generate_terraform_project_preserves_multiple_resources() -> None:
    project = ProjectIR(
        resources=[
            Resource(
                type="aws_s3_bucket",
                name="data",
                attributes={
                    "bucket": Literal("company-data"),
                },
            ),
            Resource(
                type="aws_s3_bucket",
                name="logs",
                attributes={
                    "bucket": Literal("company-logs"),
                },
            ),
        ]
    )

    result = generate_terraform_project(project)

    assert len(result.files) == 1
    assert result.files[0].path == "main.tf"

    content = result.files[0].content

    assert 'resource "aws_s3_bucket" "data" {' in content
    assert 'resource "aws_s3_bucket" "logs" {' in content