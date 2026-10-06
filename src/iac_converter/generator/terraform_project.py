from __future__ import annotations

from iac_converter.generator.terraform import TerraformGenerator
from iac_converter.ir import ProjectIR
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