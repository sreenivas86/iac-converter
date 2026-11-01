from __future__ import annotations

from iac_converter.ir import ProjectFileIR, ProjectIR
from iac_converter.parser.yaml_parser import YAMLParseError, parse_yaml
from iac_converter.project import Project


class YAMLProjectParseError(ValueError):
    """Raised when a YAML project cannot be parsed."""


def parse_yaml_project(source: str) -> ProjectIR:
    """
    Parse a complete project-level YAML document into ProjectIR.

    The YAML document represents the complete project in a single
    canonical document.
    """

    try:
        return parse_yaml(source)
    except YAMLParseError as exc:
        raise YAMLProjectParseError(f"Failed to parse YAML project: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise YAMLProjectParseError(f"Invalid YAML project: {exc}") from exc


def parse_yaml_project_files(project: Project) -> list[ProjectFileIR]:
    """
    Parse YAML project files independently while preserving relative paths.
    """
    parsed_files: list[ProjectFileIR] = []

    for project_file in project.files:
        if not project_file.path.lower().endswith((".yaml", ".yml")):
            continue

        try:
            parsed = parse_yaml(project_file.content)
        except (YAMLParseError, TypeError, ValueError) as exc:
            raise YAMLProjectParseError(
                f"Failed to parse YAML file '{project_file.path}': {exc}"
            ) from exc

        parsed_files.append(
            ProjectFileIR(
                path=project_file.path,
                project=parsed,
            )
        )

    if not parsed_files:
        raise YAMLProjectParseError("No YAML files found in project")

    return parsed_files
