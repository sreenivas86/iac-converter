from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from iac_converter.compiler import (
    parse_terraform_project,
    parse_terraform_project_files,
    parse_yaml_project,
    parse_yaml_project_files,
)
from iac_converter.generator import (
    generate_terraform,
    generate_terraform_project,
    generate_terraform_project_files,
    generate_yaml_project,
    generate_yaml_project_files,
)
from iac_converter.project import load_project, save_project


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Input path is not a file: {path}")


def _validate_input_directory(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Input path is not a directory: {path}")


def _validate_output_file(path: Path, input_path: Path) -> None:
    if path.exists() and not path.is_file():
        raise ValueError(f"Output path is not a file: {path}")

    if path.resolve() == input_path.resolve():
        raise ValueError("Input and output file paths must be different.")


def _validate_output_file_outside_directory(
    output_path: Path,
    input_directory: Path,
) -> None:
    if output_path.exists() and not output_path.is_file():
        raise ValueError(f"Output path is not a file: {output_path}")

    output_resolved = output_path.resolve()
    input_resolved = input_directory.resolve()

    if output_resolved == input_resolved or input_resolved in output_resolved.parents:
        raise ValueError(
            "Output file must not be the same as or inside the input project directory."
        )


def _validate_output_directory(path: Path, input_path: Path) -> None:
    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path is not a directory: {path}")

    if path.resolve() == input_path.resolve():
        raise ValueError("Input and output paths must be different.")


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
    if input_path.is_file():
        source = input_path.read_text(encoding="utf-8")
        project_ir = parse_yaml_project(source)
        terraform_project = generate_terraform_project(project_ir)
    else:
        project = load_project(input_path)
        parsed_files = parse_yaml_project_files(project)
        terraform_project = generate_terraform_project_files(parsed_files)

    save_project(terraform_project, output_path)


def terraform_project_to_yaml(input_path: Path, output_path: Path) -> None:
    project = load_project(input_path)

    if output_path.suffix.lower() in {".yaml", ".yml"}:
        project_ir = parse_terraform_project(project)
        _write_file(output_path, generate_yaml_project(project_ir))
    else:
        parsed_files = parse_terraform_project_files(project)
        yaml_project = generate_yaml_project_files(parsed_files)
        save_project(yaml_project, output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iac-converter",
        description="Bidirectional YAML and Terraform converter.",
    )

    try:
        package_version = version("iac-converter")
    except PackageNotFoundError:
        package_version = "unknown"

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = [
        (
            "yaml-to-terraform",
            "Convert a YAML file to a Terraform file.",
            "input",
        ),
        (
            "terraform-to-yaml",
            "Convert a Terraform project directory to YAML.",
            "input_dir",
        ),
        (
            "yaml-project-to-terraform",
            "Convert a YAML project file or directory to a Terraform project directory.",
            "input",
        ),
        (
            "terraform-project-to-yaml",
            "Convert a Terraform project directory to a YAML file or project directory.",
            "input_dir",
        ),
    ]

    for name, description, input_name in commands:
        command_parser = subparsers.add_parser(name, help=description)
        command_parser.add_argument(
            input_name,
            type=Path,
            help="Input path.",
        )
        command_parser.add_argument(
            "-o",
            "--output",
            dest="output",
            type=Path,
            required=True,
            help="Output file or directory.",
        )

        verbosity = command_parser.add_mutually_exclusive_group()
        verbosity.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed conversion information.",
        )
        verbosity.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress successful conversion messages.",
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        print(f"Running command: {args.command}", file=sys.stderr)

    try:
        if args.command == "yaml-to-terraform":
            _validate_input_file(args.input)
            _validate_output_file(args.output, args.input)
            yaml_to_terraform(args.input, args.output)

        elif args.command == "terraform-to-yaml":
            _validate_input_directory(args.input_dir)
            _validate_output_file_outside_directory(
                args.output,
                args.input_dir,
            )
            terraform_to_yaml(args.input_dir, args.output)

        elif args.command == "yaml-project-to-terraform":
            if args.input.is_file():
                _validate_input_file(args.input)
            else:
                _validate_input_directory(args.input)

            _validate_output_directory(args.output, args.input)
            yaml_project_to_terraform(args.input, args.output)

        elif args.command == "terraform-project-to-yaml":
            _validate_input_directory(args.input_dir)

            if args.output.suffix.lower() in {".yaml", ".yml"}:
                _validate_output_file_outside_directory(
                    args.output,
                    args.input_dir,
                )
            else:
                _validate_output_directory(args.output, args.input_dir)

            terraform_project_to_yaml(args.input_dir, args.output)

    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        if args.verbose:
            print(f"Output written to: {args.output}")
        else:
            print("Conversion completed successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
