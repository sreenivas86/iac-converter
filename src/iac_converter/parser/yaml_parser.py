from typing import Any

import yaml

from iac_converter.ir import (
    Block,
    CollectionExpression,
    DataSource,
    Literal,
    Module,
    Output,
    ProjectIR,
    Provider,
    RawExpression,
    Reference,
    Resource,
    Variable,
)
from iac_converter.schema.yaml_schema import YAMLProject


class YAMLParseError(ValueError):
    """Raised when YAML cannot be converted into the project schema."""


def load_yaml(source: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise YAMLParseError(f"Invalid YAML: {exc}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise YAMLParseError("YAML project root must be an object")

    return data


def parse_yaml(source: str) -> ProjectIR:
    raw = load_yaml(source)

    try:
        project = YAMLProject.model_validate(raw)
    except Exception as exc:
        raise YAMLParseError(str(exc)) from exc

    return _to_ir(project)


def _to_ir(project: YAMLProject) -> ProjectIR:
    return ProjectIR(
        version=project.version,
        terraform=project.terraform,
        providers=_parse_providers(project),
        variables=_parse_variables(project),
        resources=_parse_resources(project),
        data_sources=_parse_data_sources(project),
        outputs=_parse_outputs(project),
        modules=_parse_modules(project),
        locals=project.locals,
    )


def _parse_providers(project: YAMLProject) -> list[Provider]:
    return [
        Provider(
            name=name,
            alias=provider.alias,
            configuration=provider.properties,
        )
        for name, provider in project.providers.items()
    ]


def _parse_variables(project: YAMLProject) -> list[Variable]:
    return [
        Variable(
            name=variable.name,
            type=_convert_value(variable.type),
            description=variable.description,
            default=_convert_value(variable.default),
            sensitive=variable.sensitive,
            nullable=variable.nullable,
        )
        for variable in project.variables
    ]


def _parse_resources(project: YAMLProject) -> list[Resource]:
    return [
        Resource(
            type=resource.type,
            name=resource.name,
            attributes=_convert_mapping(resource.properties),
            blocks=_parse_blocks(resource.blocks),
            count=_convert_value(resource.count),
            for_each=_convert_value(resource.for_each),
            depends_on=_convert_value(resource.depends_on),
            lifecycle=_convert_mapping(resource.lifecycle),
            provisioners=_parse_provisioners(resource.provisioners),
        )
        for resource in project.resources
    ]


def _parse_blocks(blocks: list[Any]) -> list[Block]:
    converted: list[Block] = []

    for block in blocks:
        converted.append(
            Block(
                type=block.type,
                labels=list(block.labels),
                attributes=_convert_mapping(block.properties),
                blocks=_parse_blocks(block.blocks),
            )
        )

    return converted


def _parse_provisioners(
    provisioners: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []

    for provisioner in provisioners:
        provisioner_type = provisioner.get("type")

        if not isinstance(provisioner_type, str):
            raise YAMLParseError("Provisioner 'type' must be a string")

        properties = provisioner.get("properties", {})

        if not isinstance(properties, dict):
            raise YAMLParseError("Provisioner 'properties' must be an object")

        converted_provisioner: dict[str, Any] = {
            "type": provisioner_type,
            "properties": _convert_mapping(properties),
        }

        connection = provisioner.get("connection")

        if connection is not None:
            if not isinstance(connection, dict):
                raise YAMLParseError("Provisioner 'connection' must be an object")

            converted_provisioner["connection"] = _convert_mapping(connection)

        converted.append(converted_provisioner)

    return converted


def _parse_data_sources(project: YAMLProject) -> list[DataSource]:
    return [
        DataSource(
            type=data_source.type,
            name=data_source.name,
            attributes=_convert_mapping(data_source.properties),
        )
        for data_source in project.data_sources
    ]


def _parse_modules(project: YAMLProject) -> list[Module]:
    return [
        Module(
            name=module.name,
            source=module.source,
            arguments=_convert_mapping(module.arguments),
            count=_convert_value(module.count),
            for_each=_convert_value(module.for_each),
            depends_on=_convert_value(module.depends_on),
        )
        for module in project.modules
    ]


def _parse_outputs(project: YAMLProject) -> list[Output]:
    return [
        Output(
            name=output.name,
            value=_convert_value(output.value),
            description=output.description,
            sensitive=output.sensitive,
        )
        for output in project.outputs
    ]


def _convert_mapping(value: dict[str, Any]) -> dict[str, Any]:
    """Preserve structural mappings while converting their values."""
    return {key: _convert_value(item) for key, item in value.items()}


def _convert_value(value: Any) -> Any:
    """Convert YAML values into typed IR expressions."""
    if value is None:
        return None

    if isinstance(value, dict):
        if set(value.keys()) == {"expression"}:
            expression = value["expression"]

            if not isinstance(expression, str):
                raise YAMLParseError("'expression' must be a string")

            return RawExpression(expression)

        if set(value.keys()) == {"reference"}:
            reference = value["reference"]

            if not isinstance(reference, dict):
                raise YAMLParseError("'reference' must be an object")

            return Reference(
                resource_type=reference["resource_type"],
                resource_name=reference["resource_name"],
                attribute=reference.get("attribute"),
            )

        return CollectionExpression(
            kind="map",
            items=tuple((key, _convert_value(item)) for key, item in value.items()),
        )

    if isinstance(value, list):
        return CollectionExpression(
            kind="list",
            items=tuple(_convert_value(item) for item in value),
        )

    return Literal(value)
