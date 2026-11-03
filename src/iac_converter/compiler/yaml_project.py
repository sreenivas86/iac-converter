from __future__ import annotations

from pathlib import PurePosixPath

from iac_converter.ir import ModuleProjectIR, ProjectFileIR, ProjectIR
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


def parse_yaml_module_project(project: Project) -> ModuleProjectIR:
    """
    Parse a YAML project while keeping each module in its own IR.
    """

    parsed_files = parse_yaml_project_files(project)
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
                raise YAMLProjectParseError(
                    f"YAML file '{project_file.path}' is directly inside "
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
    """Merge one parsed YAML IR into the module project IR."""

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
