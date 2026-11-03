from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from iac_converter.validation.engine import (
    ValidationError,
    ValidationTool,
    detect_validation_tool,
    validate_project,
)


def test_detect_terraform() -> None:
    with patch(
        "iac_converter.validation.engine.shutil.which",
        return_value="terraform",
    ):
        assert detect_validation_tool(ValidationTool.TERRAFORM) == "terraform"


def test_detect_opentofu() -> None:
    with patch(
        "iac_converter.validation.engine.shutil.which",
        return_value="tofu",
    ):
        assert detect_validation_tool(ValidationTool.OPENTOFU) == "tofu"


def test_auto_prefers_terraform() -> None:
    with patch(
        "iac_converter.validation.engine.shutil.which",
        side_effect=["terraform", "tofu"],
    ):
        assert detect_validation_tool(ValidationTool.AUTO) == "terraform"


def test_auto_uses_opentofu_when_terraform_missing() -> None:
    with patch(
        "iac_converter.validation.engine.shutil.which",
        side_effect=[None, "tofu"],
    ):
        assert detect_validation_tool(ValidationTool.AUTO) == "tofu"


def test_missing_terraform_raises_error() -> None:
    with (
        patch(
            "iac_converter.validation.engine.shutil.which",
            return_value=None,
        ),
        pytest.raises(ValidationError, match="terraform CLI was not found"),
    ):
        detect_validation_tool(ValidationTool.TERRAFORM)


def test_missing_both_tools_raises_error() -> None:
    with (
        patch(
            "iac_converter.validation.engine.shutil.which",
            return_value=None,
        ),
        pytest.raises(
            ValidationError,
            match="Neither Terraform nor OpenTofu",
        ),
    ):
        detect_validation_tool(ValidationTool.AUTO)


def test_validate_project_runs_init_and_validate(tmp_path: Path) -> None:
    with (
        patch(
            "iac_converter.validation.engine.shutil.which",
            return_value="terraform",
        ),
        patch(
            "iac_converter.validation.engine._run_command",
            side_effect=[
                CompletedProcess(
                    args=["terraform", "init"],
                    returncode=0,
                    stdout="Initialized",
                    stderr="",
                ),
                CompletedProcess(
                    args=["terraform", "validate"],
                    returncode=0,
                    stdout="Success!",
                    stderr="",
                ),
            ],
        ) as mock_run,
    ):
        results = validate_project(
            tmp_path,
            ValidationTool.TERRAFORM,
        )

    assert len(results) == 2
    assert all(result.success for result in results)
    assert results[0].message == "Initialized"
    assert results[1].message == "Success!"
    assert mock_run.call_count == 2


def test_validate_project_skips_init(tmp_path: Path) -> None:
    with (
        patch(
            "iac_converter.validation.engine.shutil.which",
            return_value="tofu",
        ),
        patch(
            "iac_converter.validation.engine._run_command",
            return_value=CompletedProcess(
                args=["tofu", "validate"],
                returncode=0,
                stdout="Success!",
                stderr="",
            ),
        ) as mock_run,
    ):
        results = validate_project(
            tmp_path,
            ValidationTool.OPENTOFU,
            skip_init=True,
        )

    assert len(results) == 1
    assert results[0].success
    assert mock_run.call_args.args[0][1] == "validate"


def test_validate_project_checks_format(tmp_path: Path) -> None:
    with (
        patch(
            "iac_converter.validation.engine.shutil.which",
            return_value="terraform",
        ),
        patch(
            "iac_converter.validation.engine._run_command",
            side_effect=[
                CompletedProcess([], 0, "Initialized", ""),
                CompletedProcess([], 0, "Success!", ""),
                CompletedProcess([], 0, "", ""),
            ],
        ) as mock_run,
    ):
        results = validate_project(
            tmp_path,
            ValidationTool.TERRAFORM,
            check_format=True,
        )

    assert len(results) == 3
    assert all(result.success for result in results)
    assert mock_run.call_args.args[0][1:] == [
        "fmt",
        "-check",
        "-recursive",
    ]


def test_validate_project_stops_after_init_failure(tmp_path: Path) -> None:
    with (
        patch(
            "iac_converter.validation.engine.shutil.which",
            return_value="terraform",
        ),
        patch(
            "iac_converter.validation.engine._run_command",
            return_value=CompletedProcess(
                args=["terraform", "init"],
                returncode=1,
                stdout="",
                stderr="Initialization failed",
            ),
        ) as mock_run,
    ):
        results = validate_project(
            tmp_path,
            ValidationTool.TERRAFORM,
        )

    assert len(results) == 1
    assert not results[0].success
    assert results[0].return_code == 1
    assert mock_run.call_count == 1


def test_validate_project_rejects_missing_directory(
    tmp_path: Path,
) -> None:
    missing_directory = tmp_path / "missing"

    with pytest.raises(
        ValidationError,
        match="Project directory does not exist",
    ):
        validate_project(missing_directory)


def test_validate_project_rejects_file_path(tmp_path: Path) -> None:
    input_file = tmp_path / "main.tf"
    input_file.write_text("", encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="Project path is not a directory",
    ):
        validate_project(input_file)
