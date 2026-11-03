from __future__ import annotations

from pathlib import PurePosixPath

from iac_converter.ir import ModuleProjectIR, ProjectFileIR, ProjectIR
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
            parsed = parse_terraform(
                project_file.content,
                file_path=project_file.path,
            )
        except TerraformParseError as exc:
            raise TerraformProjectParseError(
                f"Failed to parse Terraform file '{project_file.path}': {exc}"
            ) from exc

        parsed_files.append(ProjectFileIR(path=project_file.path, project=parsed))

    return parsed_files


def parse_terraform_module_project(project: Project) -> ModuleProjectIR:
    """
    Parse a Terraform project while keeping each module in its own IR.
    """

    parsed_files = parse_terraform_project_files(project)
    root = ModuleProjectIR(path="")

    module_projects: dict[str, ModuleProjectIR] = {"": root}

    for project_file in parsed_files:
        path = PurePosixPath(project_file.path)
        parts = path.parts

        module_index = next(
            (index for index, part in enumerate(parts[:-1]) if part == "modules"),
            None,
        )

        if module_index is None:
            module_path = ""
            relative_file_path = project_file.path
        else:
            module_parts = parts[module_index + 1 : -1]

            if not module_parts:
                raise TerraformProjectParseError(
                    f"Terraform file '{project_file.path}' is directly inside "
                    "a modules directory; a module directory name is required."
                )

            module_path = PurePosixPath(
                *parts[:module_index],
                "modules",
                *module_parts,
            ).as_posix()

            relative_file_path = PurePosixPath(
                *parts[module_index + len(module_parts) + 1 :]
            ).as_posix()

        module_project = _get_or_create_module(module_projects, module_path)

        module_project.files.append(
            ProjectFileIR(
                path=relative_file_path,
                project=project_file.project,
            )
        )

        _merge_project_ir(module_project.project, project_file.project)

    return root


def _get_or_create_module(
    module_projects: dict[str, ModuleProjectIR],
    module_path: str,
) -> ModuleProjectIR:
    """Create module nodes without treating structural modules directories as modules."""

    if module_path in module_projects:
        return module_projects[module_path]

    path = PurePosixPath(module_path)
    parts = path.parts

    # Find the last structural "modules" directory.
    modules_index = max(
        (index for index, part in enumerate(parts[:-1]) if part == "modules"),
        default=-1,
    )

    if modules_index >= 0:
        parent_path = PurePosixPath(*parts[:modules_index]).as_posix()
        if parent_path == ".":
            parent_path = ""
    else:
        parent_path = ""

    parent = _get_or_create_module(module_projects, parent_path)

    module = ModuleProjectIR(path=module_path)
    parent.child_modules.append(module)
    module_projects[module_path] = module

    return module


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
    target.diagnostics.extend(source.diagnostics)
    target.locals.update(source.locals)
    target.terraform.update(source.terraform)
