from pathlib import Path

from iac_converter.compiler.terraform_project import parse_terraform_project
from iac_converter.generator import generate_terraform_project
from iac_converter.project import load_project, save_project


def test_terraform_project_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"

    source.mkdir()

    (source / "terraform.tf").write_text(
        """
terraform {
  required_version = ">= 1.6.0"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (source / "providers.tf").write_text(
        """
provider "aws" {
  region = "ap-south-1"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (source / "variables.tf").write_text(
        """
variable "bucket_name" {
  description = "S3 bucket name"
  default     = "company-data"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (source / "main.tf").write_text(
        """
resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (source / "outputs.tf").write_text(
        """
output "bucket_id" {
  value = aws_s3_bucket.data.id
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = load_project(source)

    ir = parse_terraform_project(loaded)

    generated = generate_terraform_project(ir)

    save_project(generated, output)

    generated_project = load_project(output)

    generated_paths = {project_file.path for project_file in generated_project.files}

    assert generated_paths == {
        "terraform.tf",
        "providers.tf",
        "variables.tf",
        "main.tf",
        "outputs.tf",
    }

    generated_contents = {
        project_file.path: project_file.content for project_file in generated_project.files
    }

    assert 'required_version = ">= 1.6.0"' in generated_contents["terraform.tf"]

    assert 'provider "aws"' in generated_contents["providers.tf"]

    assert 'variable "bucket_name"' in generated_contents["variables.tf"]

    assert 'resource "aws_s3_bucket" "data"' in generated_contents["main.tf"]

    assert "bucket = var.bucket_name" in generated_contents["main.tf"]

    assert 'output "bucket_id"' in generated_contents["outputs.tf"]

    assert "value = aws_s3_bucket.data.id" in generated_contents["outputs.tf"]
