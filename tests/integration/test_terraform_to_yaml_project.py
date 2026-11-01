from pathlib import Path

from iac_converter.compiler import parse_terraform_project
from iac_converter.generator import generate_yaml_project
from iac_converter.project import load_project


def test_terraform_to_yaml_project(tmp_path: Path) -> None:
    source_dir = tmp_path / "terraform-project"
    source_dir.mkdir()

    (source_dir / "terraform.tf").write_text(
        """
terraform {
  required_version = ">= 1.6.0"
}
""",
        encoding="utf-8",
    )

    (source_dir / "providers.tf").write_text(
        """
provider "aws" {
  region = "ap-south-1"
}
""",
        encoding="utf-8",
    )

    (source_dir / "variables.tf").write_text(
        """
variable "bucket_name" {
  description = "S3 bucket name"
  default     = "company-data"
}
""",
        encoding="utf-8",
    )

    (source_dir / "main.tf").write_text(
        """
resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name
}
""",
        encoding="utf-8",
    )

    (source_dir / "outputs.tf").write_text(
        """
output "bucket_id" {
  value = aws_s3_bucket.data.id
}
""",
        encoding="utf-8",
    )

    project = load_project(source_dir)

    project_ir = parse_terraform_project(project)

    yaml_source = generate_yaml_project(project_ir)

    assert 'version: "1"' in yaml_source

    assert "terraform:" in yaml_source
    assert 'required_version: ">= 1.6.0"' in yaml_source

    assert "providers:" in yaml_source
    assert "aws:" in yaml_source
    assert "region: ap-south-1" in yaml_source

    assert "variables:" in yaml_source
    assert "name: bucket_name" in yaml_source
    assert "description: S3 bucket name" in yaml_source
    assert "default: company-data" in yaml_source

    assert "resources:" in yaml_source
    assert "type: aws_s3_bucket" in yaml_source
    assert "name: data" in yaml_source

    assert "expression: var.bucket_name" in yaml_source

    assert "outputs:" in yaml_source
    assert "name: bucket_id" in yaml_source
    assert "resource_type: aws_s3_bucket" in yaml_source
    assert "resource_name: data" in yaml_source
    assert "attribute: id" in yaml_source
