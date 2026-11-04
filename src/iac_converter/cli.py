from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from iac_converter.compiler import (
    parse_terraform_module_project,
    parse_terraform_project,
    parse_yaml_module_project,
    parse_yaml_project,
)
from iac_converter.generator import (
    generate_terraform,
    generate_terraform_module_project,
    generate_terraform_project,
    generate_yaml_module_project,
    generate_yaml_project,
)
from iac_converter.ir import ModuleProjectIR, ProjectIR
from iac_converter.project import load_project, save_project
from iac_converter.validation import (
    ValidationError,
    ValidationTool,
    validate_project,
)


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


def _display_diagnostics(
    project_ir: ProjectIR,
    *,
    quiet: bool = False,
) -> None:
    for diagnostic in project_ir.diagnostics:
        severity = diagnostic.severity.value.upper()
        location = ""

        if diagnostic.file_path:
            location = diagnostic.file_path

            if diagnostic.line is not None:
                location += f":{diagnostic.line}"

                if diagnostic.column is not None:
                    location += f":{diagnostic.column}"

            location += ": "

        print(
            f"[{severity}] {diagnostic.code}: {location}{diagnostic.message}",
            file=sys.stderr,
        )

        if diagnostic.suggestion and not quiet:
            print(
                f"  Suggestion: {diagnostic.suggestion}",
                file=sys.stderr,
            )


def _display_module_diagnostics(
    module_ir: ModuleProjectIR,
    *,
    quiet: bool = False,
) -> None:
    _display_diagnostics(module_ir.project, quiet=quiet)

    for project_file in module_ir.files:
        _display_diagnostics(project_file.project, quiet=quiet)

    for child_module in module_ir.child_modules:
        _display_module_diagnostics(child_module, quiet=quiet)


def yaml_to_terraform(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    project_ir = parse_yaml_project(source)
    _write_file(output_path, generate_terraform(project_ir))


def terraform_to_yaml(
    input_path: Path,
    output_path: Path,
    *,
    quiet: bool = False,
) -> None:
    project = load_project(input_path)
    project_ir = parse_terraform_project(project)

    _display_diagnostics(project_ir, quiet=quiet)

    _write_file(output_path, generate_yaml_project(project_ir))


def yaml_project_to_terraform(
    input_path: Path,
    output_path: Path,
) -> None:
    if input_path.is_file():
        source = input_path.read_text(encoding="utf-8")
        project_ir = parse_yaml_project(source)
        terraform_project = generate_terraform_project(project_ir)
    else:
        project = load_project(input_path)
        module_ir = parse_yaml_module_project(project)
        terraform_project = generate_terraform_module_project(module_ir)

    save_project(terraform_project, output_path)


def terraform_project_to_yaml(
    input_path: Path,
    output_path: Path,
    *,
    quiet: bool = False,
) -> None:
    project = load_project(input_path)

    if output_path.suffix.lower() in {".yaml", ".yml"}:
        project_ir = parse_terraform_project(project)

        _display_diagnostics(project_ir, quiet=quiet)

        _write_file(output_path, generate_yaml_project(project_ir))
    else:
        module_ir = parse_terraform_module_project(project)

        _display_module_diagnostics(module_ir, quiet=quiet)

        yaml_project = generate_yaml_module_project(module_ir)
        save_project(yaml_project, output_path)


def _run_validation(
    project_directory: Path,
    tool: str,
    *,
    skip_init: bool,
    check_format: bool,
    verbose: bool,
    quiet: bool = False,
) -> bool:
    results = validate_project(
        project_directory,
        ValidationTool(tool),
        skip_init=skip_init,
        check_format=check_format,
    )

    for result in results:
        if not result.success:
            print(
                f"[FAILED] {result.tool}: {' '.join(result.command[1:])}",
                file=sys.stderr,
            )

            if result.message.strip():
                print(result.message.rstrip(), file=sys.stderr)

            print("Infrastructure validation failed.", file=sys.stderr)
            return False

        if not quiet:
            print(f"[PASSED] {result.tool}: {' '.join(result.command[1:])}")

            if result.message.strip():
                print(result.message.rstrip())

            if verbose:
                print(f"Exit code: {result.return_code}")

    if not quiet:
        print("Infrastructure validation completed successfully.")

    return True


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

    validation_parser = subparsers.add_parser(
        "validate",
        help="Validate a Terraform or OpenTofu project.",
        description="Initialize and validate a Terraform or OpenTofu project.",
    )

    validation_parser.add_argument(
        "project_directory",
        type=Path,
        help="Terraform or OpenTofu project directory.",
    )

    validation_parser.add_argument(
        "--tool",
        choices=[tool.value for tool in ValidationTool],
        default=ValidationTool.AUTO.value,
        help="Validation tool: terraform, tofu, or auto (default: auto).",
    )

    validation_parser.add_argument(
        "--skip-init",
        action="store_true",
        help="Skip terraform/tofu init.",
    )

    validation_parser.add_argument(
        "--check-format",
        action="store_true",
        help="Check recursive formatting without modifying files.",
    )

    validation_verbosity = validation_parser.add_mutually_exclusive_group()

    validation_verbosity.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed validation information.",
    )

    validation_verbosity.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress successful validation messages.",
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

            terraform_to_yaml(
                args.input_dir,
                args.output,
                quiet=args.quiet,
            )

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

            terraform_project_to_yaml(
                args.input_dir,
                args.output,
                quiet=args.quiet,
            )

        elif args.command == "validate":
            _validate_input_directory(args.project_directory)

            success = _run_validation(
                args.project_directory,
                args.tool,
                skip_init=args.skip_init,
                check_format=args.check_format,
                verbose=args.verbose,
                quiet=args.quiet,
            )

            return 0 if success else 1

    except (OSError, ValueError, ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:  # noqa: BLE001
        print(
            f"Unexpected error: {exc}",
            file=sys.stderr,
        )

        if args.verbose:
            import traceback

            traceback.print_exc()

        return 1
    if not args.quiet:
        if args.verbose:
            print(f"Output written to: {args.output}")
        else:
            print("Conversion completed successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
