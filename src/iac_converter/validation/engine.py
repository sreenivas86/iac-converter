from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ValidationTool(str, Enum):
    TERRAFORM = "terraform"
    OPENTOFU = "tofu"
    AUTO = "auto"


@dataclass
class ValidationResult:
    tool: str
    success: bool
    message: str
    command: list[str]
    return_code: int = 0


class ValidationError(Exception):
    """Raised when infrastructure validation fails."""


def detect_validation_tool(tool: ValidationTool) -> str:
    """Detect the requested Terraform or OpenTofu executable."""

    executable: str | None

    if tool == ValidationTool.AUTO:
        executable = shutil.which("terraform") or shutil.which("tofu")

        if executable is None:
            raise ValidationError("Neither Terraform nor OpenTofu CLI was found in PATH.")

        return executable

    executable = shutil.which(tool.value)

    if executable is None:
        raise ValidationError(f"{tool.value} CLI was not found. Install it or update PATH.")

    return executable


def _run_command(
    command: list[str],
    working_directory: Path,
) -> subprocess.CompletedProcess[str]:
    """Execute a CLI command and capture its output."""

    try:
        return subprocess.run(
            command,
            cwd=working_directory,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ValidationError(f"Unable to execute {command[0]}: {exc}") from exc


def validate_project(
    project_directory: Path,
    tool: ValidationTool = ValidationTool.AUTO,
    *,
    skip_init: bool = False,
    check_format: bool = False,
) -> list[ValidationResult]:
    """Validate a Terraform or OpenTofu project."""

    if not project_directory.exists():
        raise ValidationError(f"Project directory does not exist: {project_directory}")

    if not project_directory.is_dir():
        raise ValidationError(f"Project path is not a directory: {project_directory}")

    executable = detect_validation_tool(tool)
    tool_name = Path(executable).name.lower()

    tool_name = tool_name.removesuffix(".exe")

    results: list[ValidationResult] = []

    if not skip_init:
        init_command = [
            executable,
            "init",
            "-backend=false",
            "-input=false",
        ]

        init_result = _run_command(init_command, project_directory)

        results.append(
            ValidationResult(
                tool=tool_name,
                success=init_result.returncode == 0,
                message=init_result.stdout + init_result.stderr,
                command=init_command,
                return_code=init_result.returncode,
            )
        )

        if init_result.returncode != 0:
            return results

    validate_command = [
        executable,
        "validate",
        "-no-color",
    ]

    validate_result = _run_command(validate_command, project_directory)

    results.append(
        ValidationResult(
            tool=tool_name,
            success=validate_result.returncode == 0,
            message=validate_result.stdout + validate_result.stderr,
            command=validate_command,
            return_code=validate_result.returncode,
        )
    )

    if validate_result.returncode != 0:
        return results

    if check_format:
        format_command = [
            executable,
            "fmt",
            "-check",
            "-recursive",
        ]

        format_result = _run_command(format_command, project_directory)

        results.append(
            ValidationResult(
                tool=tool_name,
                success=format_result.returncode == 0,
                message=format_result.stdout + format_result.stderr,
                command=format_command,
                return_code=format_result.returncode,
            )
        )

    return results
