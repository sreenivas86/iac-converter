from __future__ import annotations

from pathlib import PurePosixPath

from iac_converter.generator.terraform import TerraformGenerator
from iac_converter.ir import ModuleProjectIR, ProjectFileIR, ProjectIR
from iac_converter.project import Project, ProjectFile


class TerraformProjectGenerationError(ValueError):
    """Raised when a Terraform project cannot be generated."""


def generate_terraform_project(project: ProjectIR) -> Project:
    """
    Generate a multi-file Terraform project from ProjectIR.

    Files are grouped deterministically:

    - terraform.tf
    - providers.tf
    - variables.tf
    - locals.tf
    - data.tf
    - main.tf
    - outputs.tf

    Empty files are omitted.
    """

    generator = TerraformGenerator()
    files: list[ProjectFile] = []

    sections = [
        ("terraform.tf", _terraform_section(project)),
        ("providers.tf", _providers_section(project)),
        ("variables.tf", _variables_section(project)),
        ("locals.tf", _locals_section(project)),
        ("data.tf", _data_sources_section(project)),
        ("main.tf", _resources_section(project)),
        ("outputs.tf", _outputs_section(project)),
    ]

    for filename, section in sections:
        content = generator.generate(section)

        if content.strip():
            files.append(
                ProjectFile(
                    path=filename,
                    content=content,
                )
            )

    return Project(files=files)


def _terraform_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        terraform=project.terraform,
    )


def _providers_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        providers=project.providers,
    )


def _variables_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        variables=project.variables,
    )


def _locals_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        locals=project.locals,
    )


def _data_sources_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        data_sources=project.data_sources,
    )


def _resources_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        resources=project.resources,
    )


def _outputs_section(project: ProjectIR) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        outputs=project.outputs,
    )


def generate_terraform_project_files(
    project_files: list[ProjectFileIR],
) -> Project:
    """
    Generate Terraform files while preserving YAML project paths.

    Each YAML file becomes a corresponding Terraform file.
    """

    generated_files: list[ProjectFile] = []
    generator = TerraformGenerator()

    for project_file in project_files:
        path = project_file.path

        if not path.lower().endswith((".yaml", ".yml")):
            continue

        terraform_path = path.rsplit(".", 1)[0] + ".tf"
        content = generator.generate(project_file.project)

        if content.strip():
            generated_files.append(
                ProjectFile(
                    path=terraform_path,
                    content=content,
                )
            )

    if not generated_files:
        raise TerraformProjectGenerationError(
            "No Terraform files could be generated from the YAML project"
        )

    return Project(files=generated_files)


def generate_terraform_module_project(
    module_project: ModuleProjectIR,
) -> Project:
    """
    Generate a Terraform project while preserving module directory structure.

    Each YAML file becomes a corresponding Terraform file.
    Child modules are generated recursively in their own directories.
    """

    generated_files: list[ProjectFile] = []
    _generate_module_files(module_project, generated_files)

    if not generated_files:
        raise TerraformProjectGenerationError(
            "No Terraform files could be generated from the YAML module project"
        )

    return Project(files=generated_files)


def _generate_module_files(
    module_project: ModuleProjectIR,
    generated_files: list[ProjectFile],
) -> None:
    """Generate files for one module and recursively generate child modules."""

    generator = TerraformGenerator()

    for project_file in module_project.files:
        path = project_file.path

        if not path.lower().endswith((".yaml", ".yml")):
            continue

        terraform_path = path.rsplit(".", 1)[0] + ".tf"

        if module_project.path:
            terraform_path = (PurePosixPath(module_project.path) / terraform_path).as_posix()

        content = generator.generate(project_file.project)

        if content.strip():
            generated_files.append(
                ProjectFile(
                    path=terraform_path,
                    content=content,
                )
            )

    for child_module in module_project.child_modules:
        _generate_module_files(child_module, generated_files)
