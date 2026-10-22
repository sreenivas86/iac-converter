from __future__ import annotations

import io
from typing import Any

import hcl2

from iac_converter.ir import (
    Block,
    DataSource,
    CollectionExpression,
    ConditionalExpression,
    DataSourceReference,
    FunctionCall,
    Literal,
    LocalReference,
    Output,
    ProjectIR,
    Provider,
    RawExpression,
    Reference,
    Resource,
    Variable,
    VariableReference,
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

    # Keep the terraform block itself as a mapping, while converting its
    # individual attribute values into IR values.
    return _convert_mapping(blocks[0])


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
        _convert_mapping(item) if isinstance(item, dict) else {"value": _convert_value(item)}
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


def _convert_mapping(value: dict[str, Any]) -> dict[str, Any]:
    """Convert a structural HCL mapping while keeping its outer shape."""
    return {
        key: _convert_value(item)
        for key, item in value.items()
        if key != "__is_block__"
    }


def _convert_value(
    value: Any,
) -> Any:
    """Convert python-hcl2 values into IR values.

    Lists and object/map values become CollectionExpression nodes. Structural
    mappings such as top-level block bodies are handled by _convert_mapping
    so the project model and generator can continue treating them as mappings.
    """
    if value is None:
        return None

    if isinstance(value, dict):
        return CollectionExpression(
            kind="map",
            items=tuple(
                (key, _convert_value(item))
                for key, item in value.items()
                if key != "__is_block__"
            ),
        )

    if isinstance(value, list):
        return CollectionExpression(
            kind="list",
            items=tuple(_convert_value(item) for item in value),
        )

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
            structured = _parse_structured_expression(expression)

            if structured is not None:
                return structured

            return RawExpression(expression)

        return RawExpression(original_value)

    return Literal(value)


def _extract_expression(
    value: str,
) -> str | None:
    if value.startswith("${") and value.endswith("}"):
        return value[2:-1].strip()

    return None



def _parse_structured_expression(expression: str) -> Any | None:
    """Parse common Terraform expressions into typed IR nodes.

    Supports simple references, function calls, and top-level conditional
    expressions. Anything more complex remains a RawExpression fallback.
    """
    expression = expression.strip()

    reference = _parse_reference(expression)
    if reference is not None:
        return reference

    conditional_parts = _split_conditional(expression)
    if conditional_parts is not None:
        condition_text, true_text, false_text = conditional_parts
        condition = _parse_expression_atom(condition_text)
        true_value = _parse_expression_atom(true_text)
        false_value = _parse_expression_atom(false_text)
        if condition is not None and true_value is not None and false_value is not None:
            return ConditionalExpression(
                condition=condition,
                true_value=true_value,
                false_value=false_value,
            )
        return None

    function = _parse_function_call(expression)
    if function is not None:
        return function

    return None


def _parse_expression_atom(expression: str) -> Any | None:
    expression = expression.strip()
    reference = _parse_reference(expression)
    if reference is not None:
        return reference

    function = _parse_function_call(expression)
    if function is not None:
        return function

    if expression in {"true", "false"}:
        return Literal(expression == "true")
    if expression == "null":
        return Literal(None)
    if len(expression) >= 2 and expression[0] == '"' and expression[-1] == '"':
        return Literal(expression[1:-1])
    try:
        if "." in expression:
            return Literal(float(expression))
        return Literal(int(expression))
    except ValueError:
        return None


def _parse_function_call(expression: str) -> FunctionCall | None:
    opening = expression.find("(")
    if opening <= 0 or not expression.endswith(")"):
        return None

    name = expression[:opening].strip()
    if not name.replace("_", "a").isalnum() or not name[0].isalpha():
        return None

    inner = expression[opening + 1:-1].strip()
    if not inner:
        return FunctionCall(name=name, arguments=())

    argument_texts = _split_top_level(inner, ",")
    arguments: list[Any] = []
    for argument_text in argument_texts:
        argument = _parse_expression_atom(argument_text)
        if argument is None:
            return None
        arguments.append(argument)

    return FunctionCall(name=name, arguments=tuple(arguments))


def _split_conditional(expression: str) -> tuple[str, str, str] | None:
    question_index = _find_top_level_character(expression, "?")
    if question_index < 0:
        return None

    colon_index = _find_top_level_character(expression, ":", start=question_index + 1)
    if colon_index < 0:
        return None

    condition = expression[:question_index].strip()
    true_value = expression[question_index + 1:colon_index].strip()
    false_value = expression[colon_index + 1:].strip()
    if not condition or not true_value or not false_value:
        return None
    return condition, true_value, false_value


def _split_top_level(value: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    in_string = False
    escaped = False

    for index, character in enumerate(value):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "([{}":
            depth += 1
        elif character in ")]}" :
            depth -= 1
        elif character == delimiter and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1

    parts.append(value[start:].strip())
    return parts


def _find_top_level_character(value: str, target: str, start: int = 0) -> int:
    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(value)):
        character = value[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "([{":
            depth += 1
        elif character in ")]}" :
            depth -= 1
        elif character == target and depth == 0:
            return index
    return -1

def _parse_reference(expression: str) -> Any | None:
    """Parse simple Terraform references into typed IR expressions.

    Supported references include resources, data sources, input variables,
    and local values. Meta-object references (such as ``each.value`` and
    ``self.public_ip``) and complex expressions remain RawExpression values.
    """
    expression = expression.strip()

    # Expressions containing operators, function calls, indexes, or other
    # syntax are outside the scope of simple-reference parsing.
    if any(
        char in expression
        for char in ("?", ":", "(", ")", "[", "]", ",", " ", '"')
    ):
        return None

    parts = expression.split(".")
    if any(not part for part in parts):
        return None

    # Input variable: var.bucket_name
    if len(parts) == 2 and parts[0] == "var":
        return VariableReference(name=parts[1])

    # Local value: local.bucket_prefix
    if len(parts) == 2 and parts[0] == "local":
        return LocalReference(name=parts[1])

    # Terraform meta-object references are kept as raw expressions for now.
    if parts[0] in {"each", "self"}:
        return None

    # Data source: data.aws_ami.example or data.aws_ami.example.id
    if parts[0] == "data":
        if len(parts) == 3:
            return DataSourceReference(
                data_source_type=parts[1],
                data_source_name=parts[2],
            )
        if len(parts) == 4:
            return DataSourceReference(
                data_source_type=parts[1],
                data_source_name=parts[2],
                attribute=parts[3],
            )
        return None

    # Resource: aws_s3_bucket.example or aws_s3_bucket.example.id
    if len(parts) not in (2, 3):
        return None

    return Reference(
        resource_type=parts[0],
        resource_name=parts[1],
        attribute=parts[2] if len(parts) == 3 else None,
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