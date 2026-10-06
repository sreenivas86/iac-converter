
from pathlib import Path

from iac_converter.compiler import parse_terraform_project, parse_yaml_project
from iac_converter.generator import generate_yaml_project
from iac_converter.project import load_project


def test_terraform_to_yaml_to_ir_round_trip(tmp_path: Path) -> None:
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

  tags = {
    Environment = "dev"
    Owner       = "sreenu"
  }
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

    # Terraform project -> ProjectIR
    project = load_project(source_dir)
    original_ir = parse_terraform_project(project)

    # ProjectIR -> canonical YAML
    yaml_source = generate_yaml_project(original_ir)

    # Canonical YAML -> ProjectIR
    round_trip_ir = parse_yaml_project(yaml_source)

    # ---------------------------------------------------------
    # Validate semantic preservation.
    #
    # Some Terraform parser values use Literal wrappers while
    # canonical YAML stores equivalent scalar values directly.
    # Therefore we compare the actual semantic values rather
    # than requiring identical Python wrapper types.
    # ---------------------------------------------------------

    # Project version.
    assert round_trip_ir.version == original_ir.version

    # Terraform configuration.
    assert (
        round_trip_ir.terraform["required_version"]
        == original_ir.terraform["required_version"].value
    )

    # Providers.
    assert len(round_trip_ir.providers) == len(original_ir.providers)

    round_trip_provider = round_trip_ir.providers[0]
    original_provider = original_ir.providers[0]

    assert round_trip_provider.name == original_provider.name
    assert round_trip_provider.alias == original_provider.alias

    assert (
        round_trip_provider.configuration["region"]
        == original_provider.configuration["region"].value
    )

    # Variables.
    assert len(round_trip_ir.variables) == len(original_ir.variables)

    round_trip_variable = round_trip_ir.variables[0]
    original_variable = original_ir.variables[0]

    assert round_trip_variable.name == original_variable.name
    assert (
        round_trip_variable.description
        == original_variable.description
    )
    assert (
        round_trip_variable.default
        == original_variable.default
    )

    # Resources.
    assert len(round_trip_ir.resources) == len(original_ir.resources)

    round_trip_resource = round_trip_ir.resources[0]
    original_resource = original_ir.resources[0]

    assert round_trip_resource.type == original_resource.type
    assert round_trip_resource.name == original_resource.name

    # Resource expression:
    # Terraform:
    #   bucket = var.bucket_name
    #
    # YAML:
    #   bucket:
    #     expression: var.bucket_name
    assert (
        round_trip_resource.attributes["bucket"]
        == original_resource.attributes["bucket"]
    )

    # Resource nested map.
    assert (
        round_trip_resource.attributes["tags"]["Environment"]
        == original_resource.attributes["tags"]["Environment"]
    )

    assert (
        round_trip_resource.attributes["tags"]["Owner"]
        == original_resource.attributes["tags"]["Owner"]
    )

    # Outputs.
    assert len(round_trip_ir.outputs) == len(original_ir.outputs)

    round_trip_output = round_trip_ir.outputs[0]
    original_output = original_ir.outputs[0]

    assert round_trip_output.name == original_output.name

    # The output contains a Reference, so this compares the
    # Reference objects directly.
    assert round_trip_output.value == original_output.value

