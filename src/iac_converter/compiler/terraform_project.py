from __future__ import annotations

from iac_converter.ir import ProjectFileIR, ProjectIR
from iac_converter.parser.terraform_parser import (
    TerraformParseError,
    parse_terraform,
)
from iac_converter.project import Project


class TerraformProjectParseError(ValueError):
    """Raised when a Terraform project cannot be parsed."""


def parse_terraform_project(project: Project) -> ProjectIR:
    """
    Parse all Terraform files in a project and merge them into one ProjectIR.
    """

    parsed_files = parse_terraform_project_files(project)
    merged = ProjectIR()

    for project_file in parsed_files:
        _merge_project_ir(merged, project_file.project)

    return merged


def parse_terraform_project_files(project: Project) -> list[ProjectFileIR]:
    """
    Parse Terraform files independently while preserving their relative paths.
    """

    terraform_files = project.terraform_files()

    if not terraform_files:
        raise TerraformProjectParseError("Project does not contain any Terraform (.tf) files.")

    parsed_files: list[ProjectFileIR] = []

    for project_file in terraform_files:
        try:
            parsed = parse_terraform(project_file.content)
        except TerraformParseError as exc:
            raise TerraformProjectParseError(
                f"Failed to parse Terraform file '{project_file.path}': {exc}"
            ) from exc

        parsed_files.append(ProjectFileIR(path=project_file.path, project=parsed))

    return parsed_files


def _merge_project_ir(target: ProjectIR, source: ProjectIR) -> None:
    """Merge one parsed Terraform IR into the project IR."""

    if source.version != "1":
        target.version = source.version

    target.providers.extend(source.providers)
    target.variables.extend(source.variables)
    target.resources.extend(source.resources)
    target.data_sources.extend(source.data_sources)
    target.outputs.extend(source.outputs)
    target.modules.extend(source.modules)
    target.locals.update(source.locals)
    target.terraform.update(source.terraform)
