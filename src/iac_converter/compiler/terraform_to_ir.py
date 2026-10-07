from __future__ import annotations

import io
from typing import Any

import hcl2

from iac_converter.ir import (
    Block,
    DataSource,
    Literal,
    Output,
    ProjectIR,
    Provider,
    RawExpression,
    Reference,
    Resource,
    Variable,
)


class TerraformParseError(ValueError):
    """Raised when Terraform configuration cannot be parsed."""


def parse_terraform(source: str) -> ProjectIR:
    try:
        document = hcl2.load(io.StringIO(source))
    except Exception as exc:
        raise TerraformParseError(
            f"Invalid Terraform configuration: {exc}"
        ) from exc

    return _to_ir(document)


def _to_ir(document: dict[str, Any]) -> ProjectIR:
    return ProjectIR(
        version="1",
        terraform=_parse_terraform_block(document),
        providers=_parse_providers(document),
        variables=_parse_variables(document),
        resources=_parse_resources(document),
        data_sources=_parse_data_sources(document),
        outputs=_parse_outputs(document),
        locals=_parse_locals(document),
    )


def _parse_terraform_block(
    document: dict[str, Any],
) -> dict[str, Any]:
    blocks = document.get("terraform", [])

    if not blocks:
        return {}

    # Terraform normally has one terraform block.
    return _convert_value(blocks[0])


def _parse_providers(
    document: dict[str, Any],
) -> list[Provider]:
    providers: list[Provider] = []

    for block in document.get("provider", []):
        if not isinstance(block, dict):
            continue

        for name, configuration in block.items():
            if not isinstance(configuration, dict):
                configuration = {}

            alias = configuration.get("alias")

            if alias is not None:
                alias = _unwrap_literal(alias)

            providers.append(
                Provider(
                    name=_strip_hcl_quotes(name),
                    alias=alias,
                    configuration={
                        key: _convert_value(value)
                        for key, value in configuration.items()
                        if key not in {"alias", "__is_block__"}
                    },
                )
            )

    return providers


def _parse_variables(
    document: dict[str, Any],
) -> list[Variable]:
    variables: list[Variable] = []

    for block in document.get("variable", []):
        if not isinstance(block, dict):
            continue

        for name, configuration in block.items():
            if not isinstance(configuration, dict):
                configuration = {}

            variables.append(
                Variable(
                    name=_strip_hcl_quotes(name),
                    type=_convert_value(
                        configuration.get("type")
                    ),
                    description=_unwrap_literal(
                        configuration.get("description")
                    ),
                    default=_convert_value(
                        configuration.get("default")
                    ),
                    sensitive=_unwrap_bool(
                        configuration.get("sensitive"),
                        default=False,
                    ),
                    nullable=_unwrap_optional_bool(
                        configuration.get("nullable")
                    ),
                    validation=_parse_validation(
                        configuration.get("validation")
                    ),
                )
            )

    return variables


def _parse_validation(
    value: Any,
) -> list[dict[str, Any]]:
    if value is None:
        return []

    if not isinstance(value, list):
        return []

    return [
        _convert_value(item)
        for item in value
    ]


def _parse_resources(
    document: dict[str, Any],
) -> list[Resource]:
    resources: list[Resource] = []

    for block in document.get("resource", []):
        if not isinstance(block, dict):
            continue

        for resource_type, resources_by_name in block.items():
            if not isinstance(resources_by_name, dict):
                continue

            for resource_name, configuration in resources_by_name.items():
                if not isinstance(configuration, dict):
                    configuration = {}

                resources.append(
                    Resource(
                        type=_strip_hcl_quotes(resource_type),
                        name=_strip_hcl_quotes(resource_name),
                        attributes=_parse_resource_attributes(
                            configuration
                        ),
                        blocks=_parse_nested_blocks(
                            configuration
                        ),
                        count=_convert_value(
                            configuration.get("count")
                        ),
                        for_each=_convert_value(
                            configuration.get("for_each")
                        ),
                        depends_on=_convert_value(
                            configuration.get("depends_on", [])
                        ),
                        lifecycle=_convert_block(
                            configuration.get("lifecycle")
                        ),
                        provisioners=_parse_provisioners(
                            configuration.get("provisioner")
                        ),
                    )
                )

    return resources


def _parse_nested_blocks(
    configuration: dict[str, Any],
) -> list[Block]:
    blocks: list[Block] = []

    meta_arguments = {
        "count",
        "for_each",
        "depends_on",
        "lifecycle",
        "provisioner",
        "connection",
        "__is_block__",
    }

    for key, value in configuration.items():
        if key in meta_arguments:
            continue

        if not isinstance(value, list):
            continue

        for item in value:
            if not isinstance(item, dict):
                continue

            if "__is_block__" not in item:
                continue

            blocks.append(
                Block(
                    type=_strip_hcl_quotes(key),
                    attributes=_parse_block_attributes(item),
                    blocks=_parse_nested_blocks(item),
                )
            )

    return blocks


def _parse_block_attributes(
    configuration: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: _convert_value(value)
        for key, value in configuration.items()
        if key != "__is_block__"
        and not _is_nested_block_value(value)
    }


def _parse_provisioners(
    value: Any,
) -> list[dict[str, Any]]:
    """Convert Terraform provisioner blocks into IR dictionaries."""
    if value is None:
        return []

    if not isinstance(value, list):
        return []

    provisioners: list[dict[str, Any]] = []

    for block in value:
        if not isinstance(block, dict):
            continue

        for provisioner_type, configuration in block.items():
            if provisioner_type == "__is_block__":
                continue

            if not isinstance(configuration, dict):
                configuration = {}

            provisioner: dict[str, Any] = {
                "type": _strip_hcl_quotes(provisioner_type),
                "properties": {},
            }

            for key, item in configuration.items():
                if key == "__is_block__":
                    continue

                if key == "connection":
                    provisioner["connection"] = _convert_block(item)
                    continue

                provisioner["properties"][key] = _convert_value(item)

            provisioners.append(provisioner)

    return provisioners


def _parse_resource_attributes(
    configuration: dict[str, Any],
) -> dict[str, Any]:
    meta_arguments = {
        "count",
        "for_each",
        "depends_on",
        "lifecycle",
        "provisioner",
        "connection",
        "__is_block__",
    }

    return {
        key: _convert_value(value)
        for key, value in configuration.items()
        if key not in meta_arguments
        and not _is_nested_block_value(value)
    }


def _is_nested_block_value(
    value: Any,
) -> bool:
    if not isinstance(value, list):
        return False

    return any(
        isinstance(item, dict) and "__is_block__" in item
        for item in value
    )


def _parse_data_sources(
    document: dict[str, Any],
) -> list[DataSource]:
    data_sources: list[DataSource] = []

    for block in document.get("data", []):
        if not isinstance(block, dict):
            continue

        for data_type, data_by_name in block.items():
            if not isinstance(data_by_name, dict):
                continue

            for name, configuration in data_by_name.items():
                if not isinstance(configuration, dict):
                    configuration = {}

                data_sources.append(
                    DataSource(
                        type=_strip_hcl_quotes(data_type),
                        name=_strip_hcl_quotes(name),
                        attributes={
                            key: _convert_value(value)
                            for key, value in configuration.items()
                            if key != "__is_block__"
                        },
                        depends_on=_convert_value(
                            configuration.get("depends_on", [])
                        ),
                    )
                )

    return data_sources


def _parse_outputs(
    document: dict[str, Any],
) -> list[Output]:
    outputs: list[Output] = []

    for block in document.get("output", []):
        if not isinstance(block, dict):
            continue

        for name, configuration in block.items():
            if not isinstance(configuration, dict):
                configuration = {}

            outputs.append(
                Output(
                    name=_strip_hcl_quotes(name),
                    value=_convert_value(
                        configuration.get("value")
                    ),
                    description=_unwrap_literal(
                        configuration.get("description")
                    ),
                    sensitive=_unwrap_bool(
                        configuration.get("sensitive"),
                        default=False,
                    ),
                    depends_on=_convert_value(
                        configuration.get("depends_on")
                    ),
                )
            )

    return outputs


def _parse_locals(
    document: dict[str, Any],
) -> dict[str, Any]:
    blocks = document.get("locals", [])

    if not blocks:
        return {}

    result: dict[str, Any] = {}

    for block in blocks:
        if isinstance(block, dict):
            for key, value in block.items():
                if key == "__is_block__":
                    continue

                result[key] = _convert_value(value)

    return result


def _convert_block(
    value: Any,
) -> dict[str, Any]:
    """Convert an HCL block/object into a plain IR dictionary."""
    if value is None:
        return {}

    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], dict):
            return {
                key: _convert_value(item)
                for key, item in value[0].items()
                if key != "__is_block__"
            }

        return {
            str(index): _convert_value(item)
            for index, item in enumerate(value)
        }

    if isinstance(value, dict):
        return {
            key: _convert_value(item)
            for key, item in value.items()
            if key != "__is_block__"
        }

    return {}


def _convert_value(
    value: Any,
) -> Any:
    """Convert python-hcl2 values into IR values."""
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            key: _convert_value(item)
            for key, item in value.items()
            if key != "__is_block__"
        }

    if isinstance(value, list):
        return [
            _convert_value(item)
            for item in value
        ]

    if isinstance(value, str):
        return _convert_string(value)

    if isinstance(value, (bool, int, float)):
        return Literal(value)

    return Literal(value)


def _convert_string(
    value: str,
) -> Any:
    """Convert an HCL string/expression into the IR."""
    original_value = value.strip()
    value = _strip_hcl_quotes(original_value)

    # Preserve Terraform interpolation strings such as:
    # "echo ${self.id}"
    # "arn:${var.region}:${var.account_id}"
    if "${" in value:
        expression = _extract_expression(value)

        if expression is not None:
            reference = _parse_reference(expression)

            if reference is not None:
                return reference

            return RawExpression(expression)

        return RawExpression(original_value)

    return Literal(value)


def _extract_expression(
    value: str,
) -> str | None:
    if value.startswith("${") and value.endswith("}"):
        return value[2:-1].strip()

    return None


def _parse_reference(
    expression: str,
) -> Reference | None:
    """Parse simple Terraform resource/data references.

    Supported:

        aws_s3_bucket.data
        aws_s3_bucket.data.id

    Variable, local, and Terraform meta-object references such as:

        var.bucket_name
        local.bucket_prefix
        each.value
        self.public_ip

    remain RawExpression.

    Complex expressions remain RawExpression.
    """
    expression = expression.strip()

    if any(
        char in expression
        for char in ("?", ":", "(", ")", "[", "]", ",")
    ):
        return None

    parts = expression.split(".")

    if len(parts) not in (2, 3):
        return None

    # These are Terraform expressions, not resource references.
    if parts[0] in {"var", "local", "each", "self"}:
        return None

    resource_type = parts[0]
    resource_name = parts[1]
    attribute = parts[2] if len(parts) == 3 else None

    if not resource_type or not resource_name:
        return None

    if attribute is not None and not attribute:
        return None

    return Reference(
        resource_type=resource_type,
        resource_name=resource_name,
        attribute=attribute,
    )


def _strip_hcl_quotes(
    value: str,
) -> str:
    value = value.strip()

    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]

    return value


def _unwrap_literal(
    value: Any,
) -> Any:
    if isinstance(value, Literal):
        return value.value

    if isinstance(value, str):
        return _strip_hcl_quotes(value)

    return value


def _unwrap_bool(
    value: Any,
    *,
    default: bool,
) -> bool:
    if value is None:
        return default

    value = _unwrap_literal(value)

    return bool(value)


def _unwrap_optional_bool(
    value: Any,
) -> bool | None:
    if value is None:
        return None

    value = _unwrap_literal(value)

    return bool(value)


def _unwrap_string(
    value: Any,
) -> Any:
    if not isinstance(value, str):
        return value

    value = value.strip()

    # python-hcl2 can return quoted HCL strings for block labels.
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]

    return value