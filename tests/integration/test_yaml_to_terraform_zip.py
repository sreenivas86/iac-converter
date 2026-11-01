from pathlib import Path
from zipfile import ZipFile

from iac_converter.compiler import parse_yaml_project
from iac_converter.generator import generate_terraform_project
from iac_converter.project import save_project_zip


def test_yaml_to_terraform_zip(tmp_path: Path) -> None:
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

    project_ir = parse_yaml_project(source)
    terraform_project = generate_terraform_project(project_ir)

    archive_path = tmp_path / "terraform-project.zip"

    save_project_zip(
        terraform_project,
        archive_path,
    )

    assert archive_path.exists()
    assert archive_path.is_file()

    with ZipFile(archive_path, "r") as archive:
        files = {name: archive.read(name).decode("utf-8") for name in archive.namelist()}

    assert "terraform.tf" in files
    assert "providers.tf" in files
    assert "variables.tf" in files
    assert "main.tf" in files
    assert "outputs.tf" in files

    assert 'required_version = ">= 1.6.0"' in files["terraform.tf"]

    assert 'provider "aws"' in files["providers.tf"]
    assert 'region = "ap-south-1"' in files["providers.tf"]

    assert 'variable "bucket_name"' in files["variables.tf"]
    assert 'default = "company-data"' in files["variables.tf"]

    assert 'resource "aws_s3_bucket" "data"' in files["main.tf"]
    assert "bucket = var.bucket_name" in files["main.tf"]

    assert 'output "bucket_id"' in files["outputs.tf"]
    assert "value = aws_s3_bucket.data.id" in files["outputs.tf"]
