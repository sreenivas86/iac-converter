from __future__ import annotations

from typing import Any

import yaml

from iac_converter.ir import (
    Literal,
    ModuleReference,
    ProjectFileIR,
    ProjectIR,
    RawExpression,
    Reference,
)
from iac_converter.project import Project, ProjectFile


class YAMLProjectGenerationError(ValueError):
    """Raised when a YAML project cannot be generated."""


def generate_yaml_project(project: ProjectIR) -> str:
    """
    Generate the canonical project YAML document.

    The generated document represents the complete ProjectIR in one
    YAML document.
    """

    document: dict[str, Any] = {
        "version": str(project.version),
    }

    if project.terraform:
        document["terraform"] = _convert_mapping(project.terraform)

    if project.providers:
        document["providers"] = {
            provider.name: _provider_to_dict(provider) for provider in project.providers
        }

    if project.variables:
        document["variables"] = [_variable_to_dict(variable) for variable in project.variables]

    if project.locals:
        document["locals"] = _convert_mapping(project.locals)

    if project.data_sources:
        document["data_sources"] = [
            _data_source_to_dict(data_source) for data_source in project.data_sources
        ]

    if project.resources:
        document["resources"] = [_resource_to_dict(resource) for resource in project.resources]

    if project.modules:
        document["modules"] = [_module_to_dict(module) for module in project.modules]
    if project.outputs:
        document["outputs"] = [_output_to_dict(output) for output in project.outputs]

    try:
        content = yaml.safe_dump(
            document,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    except yaml.YAMLError as exc:
        raise YAMLProjectGenerationError(f"Failed to generate YAML project: {exc}") from exc

    # Keep the project version visually consistent with our YAML contract.
    if content.startswith("version: '1'"):
        content = content.replace(
            "version: '1'",
            'version: "1"',
            1,
        )

    # Keep Terraform required_version visually consistent with
    # our canonical YAML contract.
    if "required_version: '>= 1.6.0'" in content:
        content = content.replace(
            "required_version: '>= 1.6.0'",
            'required_version: ">= 1.6.0"',
            1,
        )

    return content


def generate_yaml_project_files(
    project_files: list[ProjectFileIR],
) -> Project:
    """
    Generate YAML files while preserving the original Terraform file paths.
    """

    generated_files: list[ProjectFile] = []

    for project_file in project_files:
        path = project_file.path

        if not path.lower().endswith(".tf"):
            continue

        yaml_path = path[:-3] + ".yaml"
        content = generate_yaml_project(project_file.project)

        if content.strip():
            generated_files.append(ProjectFile(path=yaml_path, content=content))

    if not generated_files:
        raise YAMLProjectGenerationError(
            "No YAML files could be generated from the Terraform project"
        )

    return Project(files=generated_files)


def _provider_to_dict(provider: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "properties": _convert_mapping(provider.configuration),
    }

    if provider.alias is not None:
        result["alias"] = provider.alias

    return result


def _variable_to_dict(variable: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": variable.name,
    }

    if variable.type is not None:
        result["type"] = _convert_value(variable.type)

    if variable.description is not None:
        result["description"] = variable.description

    if variable.default is not None:
        result["default"] = _convert_value(variable.default)

    if variable.sensitive:
        result["sensitive"] = True

    if variable.nullable is not None:
        result["nullable"] = variable.nullable

    if variable.validation:
        result["validation"] = _convert_value(variable.validation)

    return result


def _resource_to_dict(resource: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": resource.type,
        "name": resource.name,
        "properties": _convert_mapping(resource.attributes),
    }

    if resource.count is not None:
        result["count"] = _convert_value(resource.count)

    if resource.for_each is not None:
        result["for_each"] = _convert_value(resource.for_each)

    if resource.depends_on:
        result["depends_on"] = _convert_value(resource.depends_on)

    if resource.lifecycle:
        result["lifecycle"] = _convert_value(resource.lifecycle)

    if resource.provisioners:
        result["provisioners"] = _convert_value(resource.provisioners)

    return result


def _data_source_to_dict(data_source: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": data_source.type,
        "name": data_source.name,
        "properties": _convert_mapping(data_source.attributes),
    }

    if data_source.depends_on:
        result["depends_on"] = _convert_value(data_source.depends_on)

    return result


def _module_to_dict(module: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": module.name,
        "source": module.source,
        "arguments": _convert_mapping(module.arguments),
    }

    if module.count is not None:
        result["count"] = _convert_value(module.count)

    if module.for_each is not None:
        result["for_each"] = _convert_value(module.for_each)

    if module.depends_on:
        result["depends_on"] = _convert_value(module.depends_on)

    return result


def _output_to_dict(output: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": output.name,
        "value": _convert_value(output.value),
    }

    if output.description is not None:
        result["description"] = output.description

    if output.sensitive:
        result["sensitive"] = True

    if output.depends_on:
        result["depends_on"] = _convert_value(output.depends_on)

    return result


def _convert_mapping(value: dict[str, Any]) -> dict[str, Any]:
    return {key: _convert_value(item) for key, item in value.items()}


def _convert_value(value: Any) -> Any:
    if isinstance(value, Literal):
        return _convert_value(value.value)

    if isinstance(value, Reference):
        result: dict[str, Any] = {
            "reference": {
                "resource_type": value.resource_type,
                "resource_name": value.resource_name,
            }
        }

        if value.attribute is not None:
            result["reference"]["attribute"] = value.attribute

        return result
    if isinstance(value, ModuleReference):
        return {
            "module_reference": {
                "module_name": value.module_name,
                "output_name": value.output_name,
            }
        }

    if isinstance(value, RawExpression):
        return {
            "expression": value.value,
        }

    if isinstance(value, dict):
        return {key: _convert_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_convert_value(item) for item in value]

    if isinstance(value, tuple):
        return [_convert_value(item) for item in value]

    return value
