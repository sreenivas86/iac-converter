from pathlib import Path

from iac_converter.cli import main

YAML_SOURCE = """
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
"""


def test_cli_yaml_to_terraform(tmp_path: Path) -> None:
    input_file = tmp_path / "project.yaml"
    output_file = tmp_path / "main.tf"

    input_file.write_text(YAML_SOURCE, encoding="utf-8")

    result = main(
        [
            "yaml-to-terraform",
            str(input_file),
            "--output",
            str(output_file),
        ]
    )

    assert result == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert 'resource "aws_s3_bucket" "data"' in content
    assert 'bucket = "company-data"' in content


def test_cli_terraform_to_yaml(tmp_path: Path) -> None:
    input_dir = tmp_path / "terraform"
    input_dir.mkdir()

    (input_dir / "main.tf").write_text(
        """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
        encoding="utf-8",
    )

    output_file = tmp_path / "project.yaml"

    result = main(
        [
            "terraform-to-yaml",
            str(input_dir),
            "--output",
            str(output_file),
        ]
    )

    assert result == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "resources:" in content
    assert "aws_s3_bucket" in content
    assert "company-data" in content


def test_cli_yaml_project_to_terraform(tmp_path: Path) -> None:
    input_file = tmp_path / "project.yaml"
    output_dir = tmp_path / "terraform"

    input_file.write_text(YAML_SOURCE, encoding="utf-8")

    result = main(
        [
            "yaml-project-to-terraform",
            str(input_file),
            "--output",
            str(output_dir),
        ]
    )

    assert result == 0
    assert output_dir.is_dir()
    assert (output_dir / "terraform.tf").exists()
    assert (output_dir / "providers.tf").exists()
    assert (output_dir / "main.tf").exists()


def test_cli_terraform_project_to_yaml(tmp_path: Path) -> None:
    input_dir = tmp_path / "terraform"
    input_dir.mkdir()

    (input_dir / "main.tf").write_text(
        """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}
""",
        encoding="utf-8",
    )

    output_file = tmp_path / "project.yaml"

    result = main(
        [
            "terraform-project-to-yaml",
            str(input_dir),
            "--output",
            str(output_file),
        ]
    )

    assert result == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "resources:" in content
    assert "aws_s3_bucket" in content


def test_cli_returns_error_for_invalid_yaml(tmp_path: Path) -> None:
    input_file = tmp_path / "invalid.yaml"
    output_file = tmp_path / "main.tf"

    input_file.write_text(
        "version: [invalid",
        encoding="utf-8",
    )

    result = main(
        [
            "yaml-to-terraform",
            str(input_file),
            "--output",
            str(output_file),
        ]
    )

    assert result == 1
    assert not output_file.exists()


def test_cli_returns_error_for_missing_input(tmp_path: Path) -> None:
    input_file = tmp_path / "missing.yaml"
    output_file = tmp_path / "main.tf"

    result = main(
        [
            "yaml-to-terraform",
            str(input_file),
            "--output",
            str(output_file),
        ]
    )

    assert result == 1
    assert not output_file.exists()


def test_cli_displays_version(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0

    output = capsys.readouterr().out
    assert output.startswith("iac-converter ")
    assert "0.1.0" in output


def test_cli_quiet_suppresses_success_message(
    tmp_path: Path,
    capsys,
) -> None:
    input_file = tmp_path / "project.yaml"
    output_file = tmp_path / "main.tf"

    input_file.write_text(YAML_SOURCE, encoding="utf-8")

    result = main(
        [
            "yaml-to-terraform",
            str(input_file),
            "--output",
            str(output_file),
            "--quiet",
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert captured.out == ""
    assert captured.err == ""
    assert output_file.exists()


def test_cli_verbose_displays_conversion_information(
    tmp_path: Path,
    capsys,
) -> None:
    input_file = tmp_path / "project.yaml"
    output_file = tmp_path / "main.tf"

    input_file.write_text(YAML_SOURCE, encoding="utf-8")

    result = main(
        [
            "yaml-to-terraform",
            str(input_file),
            "--output",
            str(output_file),
            "--verbose",
        ]
    )

    captured = capsys.readouterr()

    assert result == 0
    assert "Running command: yaml-to-terraform" in captured.err
    assert f"Output written to: {output_file}" in captured.out
    assert output_file.exists()
