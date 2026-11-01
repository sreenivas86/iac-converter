from __future__ import annotations

import argparse
import sys
from pathlib import Path

from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import (
    generate_terraform,
    generate_terraform_project,
    generate_yaml_project,
)
from iac_converter.project import (
    load_project,
    save_project,
)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def yaml_to_terraform(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    project_ir = parse_yaml_project(source)
    _write_file(output_path, generate_terraform(project_ir))


def terraform_to_yaml(input_path: Path, output_path: Path) -> None:
    project = load_project(input_path)
    project_ir = parse_terraform_project(project)
    _write_file(output_path, generate_yaml_project(project_ir))


def yaml_project_to_terraform(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    project_ir = parse_yaml_project(source)
    terraform_project = generate_terraform_project(project_ir)
    save_project(terraform_project, output_path)


def terraform_project_to_yaml(input_path: Path, output_path: Path) -> None:
    project = load_project(input_path)
    project_ir = parse_terraform_project(project)
    _write_file(output_path, generate_yaml_project(project_ir))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iac-converter",
        description="Bidirectional YAML and Terraform converter.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = [
        (
            "yaml-to-terraform",
            "Convert a YAML file to a Terraform file.",
            "input",
            "output",
        ),
        (
            "terraform-to-yaml",
            "Convert a Terraform project directory to YAML.",
            "input_dir",
            "output_file",
        ),
        (
            "yaml-project-to-terraform",
            "Convert a YAML project file to a Terraform project directory.",
            "input",
            "output_dir",
        ),
        (
            "terraform-project-to-yaml",
            "Convert a Terraform project directory to YAML.",
            "input_dir",
            "output_file",
        ),
    ]

    for name, description, input_name, output_name in commands:
        command_parser = subparsers.add_parser(name, help=description)
        command_parser.add_argument(input_name, type=Path, help="Input path.")
        command_parser.add_argument(
            "-o",
            "--output",
            dest="output",
            type=Path,
            required=True,
            help="Output file or directory.",
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "yaml-to-terraform":
            yaml_to_terraform(args.input, args.output)
        elif args.command == "terraform-to-yaml":
            terraform_to_yaml(args.input_dir, args.output)
        elif args.command == "yaml-project-to-terraform":
            yaml_project_to_terraform(args.input, args.output)
        elif args.command == "terraform-project-to-yaml":
            terraform_project_to_yaml(args.input_dir, args.output)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Conversion completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
