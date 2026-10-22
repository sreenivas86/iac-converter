from __future__ import annotations

import json
from typing import Any

from iac_converter.ir import (
    Block,
    DataSource,
    ConditionalExpression,
    CollectionExpression,
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


class TerraformGenerationError(ValueError):
    """Raised when IR cannot be converted to Terraform."""


class TerraformGenerator:
    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def generate(self, project: ProjectIR) -> str:
        sections: list[str] = []

        if project.terraform:
            sections.append(self._terraform_block(project.terraform))

        for provider in project.providers:
            sections.append(self._provider_block(provider))

        for variable in project.variables:
            sections.append(self._variable_block(variable))

        if project.locals:
            sections.append(self._locals_block(project.locals))

        for data_source in project.data_sources:
            sections.append(self._data_source_block(data_source))

        for resource in project.resources:
            sections.append(self._resource_block(resource))

        for output in project.outputs:
            sections.append(self._output_block(output))

        return (
            "\n\n".join(
                section for section in sections if section.strip()
            )
            + "\n"
        )

    # ------------------------------------------------------------------
    # Top-level blocks
    # ------------------------------------------------------------------

    def _terraform_block(
        self,
        configuration: dict[str, Any],
    ) -> str:
        body = self._render_arguments(
            configuration,
            level=1,
        )

        return self._block(
            header="terraform",
            body=body,
            level=0,
        )

    def _provider_block(
        self,
        provider: Provider,
    ) -> str:
        arguments = dict(provider.configuration)

        if provider.alias is not None:
            arguments["alias"] = provider.alias

        body = self._render_arguments(
            arguments,
            level=1,
        )

        return self._block(
            header=f'provider "{provider.name}"',
            body=body,
            level=0,
        )

    def _variable_block(
        self,
        variable: Variable,
    ) -> str:
        arguments: list[tuple[str, Any]] = []

        if variable.type is not None:
            arguments.append(("type", variable.type))

        if variable.description is not None:
            arguments.append(
                ("description", variable.description)
            )

        if variable.default is not None:
            arguments.append(("default", variable.default))

        if variable.sensitive:
            arguments.append(("sensitive", True))

        if variable.nullable is not None:
            arguments.append(("nullable", variable.nullable))

        body = self._render_arguments(
            dict(arguments),
            level=1,
            special_expression_keys={"type"},
        )

        return self._block(
            header=f'variable "{variable.name}"',
            body=body,
            level=0,
        )

    def _locals_block(
        self,
        locals_values: dict[str, Any],
    ) -> str:
        body = self._render_arguments(
            locals_values,
            level=1,
            expression_values=True,
        )

        return self._block(
            header="locals",
            body=body,
            level=0,
        )

    def _data_source_block(
        self,
        data_source: DataSource,
    ) -> str:
        body = self._render_arguments(
            data_source.attributes,
            level=1,
        )

        if data_source.depends_on:
            body += self._render_argument(
                "depends_on",
                data_source.depends_on,
                level=1,
            )

        return self._block(
            header=f'data "{data_source.type}" "{data_source.name}"',
            body=body,
            level=0,
        )

    def _resource_block(
        self,
        resource: Resource,
    ) -> str:
        lines: list[str] = []

        # Regular resource attributes.
        attributes = self._render_arguments(
            resource.attributes,
            level=1,
        )

        if attributes:
            lines.extend(attributes.splitlines())

        # Nested resource blocks.
        for block in resource.blocks:
            lines.append(
                self._render_block(
                    block,
                    level=1,
                )
            )

        # Meta arguments.
        if resource.count is not None:
            lines.append(
                self._render_argument(
                    "count",
                    resource.count,
                    level=1,
                    expression=True,
                )
            )

        if resource.for_each is not None:
            lines.append(
                self._render_argument(
                    "for_each",
                    resource.for_each,
                    level=1,
                    expression=True,
                )
            )

        if resource.depends_on:
            lines.append(
                self._render_argument(
                    "depends_on",
                    resource.depends_on,
                    level=1,
                )
            )

        # Lifecycle block.
        if resource.lifecycle:
            lines.append(
                self._render_lifecycle_block(
                    resource.lifecycle,
                    level=1,
                )
            )

        # Provisioners.
        for provisioner in resource.provisioners:
            lines.append(
                self._render_provisioner_block(
                    provisioner,
                    level=1,
                )
            )

        body = "\n".join(
            line for line in lines if line
        )

        return self._block(
            header=f'resource "{resource.type}" "{resource.name}"',
            body=body,
            level=0,
        )

    def _output_block(
        self,
        output: Output,
    ) -> str:
        arguments: dict[str, Any] = {
            "value": output.value,
        }

        if output.description is not None:
            arguments["description"] = output.description

        if output.sensitive:
            arguments["sensitive"] = True

        if output.depends_on:
            arguments["depends_on"] = output.depends_on

        body = self._render_arguments(
            arguments,
            level=1,
        )

        return self._block(
            header=f'output "{output.name}"',
            body=body,
            level=0,
        )

    # ------------------------------------------------------------------
    # Nested blocks
    # ------------------------------------------------------------------

    def _render_block(
        self,
        block: Block,
        level: int,
    ) -> str:
        """Render a nested Terraform block recursively."""
        indentation = self._indent(level)

        header = block.type

        if block.labels:
            header += " " + " ".join(
                json.dumps(label)
                for label in block.labels
            )

        lines: list[str] = []

        # Block attributes.
        if block.attributes:
            attributes = self._render_arguments(
                block.attributes,
                level=level + 1,
            )

            if attributes:
                lines.extend(
                    attributes.splitlines()
                )

        # Child nested blocks.
        for child in block.blocks:
            lines.append(
                self._render_block(
                    child,
                    level=level + 1,
                )
            )

        body = "\n".join(
            line for line in lines if line
        )

        if not body:
            return f"{indentation}{header} {{}}"

        return (
            f"{indentation}{header} {{\n"
            f"{body}\n"
            f"{indentation}}}"
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_arguments(
        self,
        arguments: dict[str, Any],
        level: int,
        *,
        expression_values: bool = False,
        special_expression_keys: set[str] | None = None,
    ) -> str:
        special_expression_keys = special_expression_keys or set()

        lines: list[str] = []

        for key, value in arguments.items():
            lines.append(
                self._render_argument(
                    key,
                    value,
                    level=level,
                    expression=(
                        expression_values
                        or key in special_expression_keys
                    ),
                )
            )

        return "\n".join(lines)

    def _render_argument(
        self,
        name: str,
        value: Any,
        level: int,
        *,
        expression: bool = False,
    ) -> str:
        indentation = self._indent(level)

        rendered = self._render_value(
            value,
            expression=expression,
        )

        return f"{indentation}{name} = {rendered}"

    def _render_lifecycle_block(
        self,
        values: dict[str, Any],
        level: int,
    ) -> str:
        indentation = self._indent(level)

        lines: list[str] = []

        for key, value in values.items():
            if key == "ignore_changes":
                lines.append(
                    self._render_argument(
                        key,
                        value,
                        level=level + 1,
                        expression=True,
                    )
                )
            else:
                lines.append(
                    self._render_argument(
                        key,
                        value,
                        level=level + 1,
                    )
                )

        body = "\n".join(lines)

        return (
            f"{indentation}lifecycle {{\n"
            f"{body}\n"
            f"{indentation}}}"
        )

    def _render_provisioner_block(
        self,
        provisioner: dict[str, Any],
        level: int,
    ) -> str:
        provisioner_type = provisioner.get("type")

        if not isinstance(provisioner_type, str):
            raise TerraformGenerationError(
                "Provisioner 'type' must be a string"
            )

        properties = provisioner.get(
            "properties",
            {},
        )

        if not isinstance(properties, dict):
            raise TerraformGenerationError(
                "Provisioner 'properties' must be an object"
            )

        indentation = self._indent(level)

        lines: list[str] = [
            f'{indentation}provisioner "{provisioner_type}" {{'
        ]

        if properties:
            lines.append(
                self._render_arguments(
                    properties,
                    level=level + 1,
                )
            )

        connection = provisioner.get("connection")

        if connection is not None:
            if not isinstance(connection, dict):
                raise TerraformGenerationError(
                    "Provisioner 'connection' must be an object"
                )

            lines.append(
                self._render_connection_block(
                    connection,
                    level=level + 1,
                )
            )

        lines.append(
            f"{indentation}}}"
        )

        return "\n".join(lines)

    def _render_connection_block(
        self,
        connection: dict[str, Any],
        level: int,
    ) -> str:
        indentation = self._indent(level)

        body = self._render_arguments(
            connection,
            level=level + 1,
        )

        return (
            f"{indentation}connection {{\n"
            f"{body}\n"
            f"{indentation}}}"
        )

    def _render_nested_block(
        self,
        name: str,
        values: dict[str, Any],
        level: int,
    ) -> str:
        indentation = self._indent(level)

        body = self._render_arguments(
            values,
            level=level + 1,
        )

        return (
            f"{indentation}{name} {{\n"
            f"{body}\n"
            f"{indentation}}}"
        )

    def _render_value(
        self,
        value: Any,
        *,
        expression: bool = False,
    ) -> str:
        if isinstance(value, Literal):
            return self._render_literal(
                value.value,
                expression=expression,
            )

        if isinstance(
            value,
            (
                Reference,
                DataSourceReference,
                VariableReference,
                LocalReference,
            ),
        ):
            return value.to_string()

        if isinstance(value, RawExpression):
            return value.value

        if isinstance(value, FunctionCall):
            # Function arguments can be literals (which need quoting), typed
            # references, or nested expressions. Let each argument's type
            # determine its rendering rather than forcing expression mode.
            arguments = ", ".join(
                self._render_value(argument)
                for argument in value.arguments
            )
            return f"{value.name}({arguments})"

        if isinstance(value, ConditionalExpression):
            condition = self._render_value(value.condition, expression=True)
            # Conditional branches may be string literals, so render them
            # normally to preserve their quotes in generated HCL.
            true_value = self._render_value(value.true_value)
            false_value = self._render_value(value.false_value)
            return f"{condition} ? {true_value} : {false_value}"

        if isinstance(value, CollectionExpression):
            if value.kind in {"list", "tuple"}:
                return self._render_list(
                    list(value.items),
                    expression=expression,
                )
            if value.kind == "map":
                try:
                    mapping = dict(value.items)
                except (TypeError, ValueError) as exc:
                    raise TerraformGenerationError(
                        "Map CollectionExpression items must be key/value pairs"
                    ) from exc
                return self._render_object(mapping)
            raise TerraformGenerationError(
                f"Unsupported collection kind: {value.kind}"
            )

        if isinstance(value, dict):
            return self._render_object(value)

        if isinstance(value, list):
            return self._render_list(
                value,
                expression=expression,
            )

        if isinstance(value, tuple):
            return self._render_list(
                list(value),
                expression=expression,
            )

        return self._render_literal(
            value,
            expression=expression,
        )

    def _render_literal(
        self,
        value: Any,
        *,
        expression: bool = False,
    ) -> str:
        if value is None:
            return "null"

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, str):
            if expression:
                return value

            return json.dumps(value)

        if isinstance(value, dict):
            return self._render_object(value)

        if isinstance(value, list):
            return self._render_list(
                value,
                expression=expression,
            )

        raise TerraformGenerationError(
            f"Unsupported literal type: {type(value).__name__}"
        )

    def _render_object(
        self,
        value: dict[str, Any],
    ) -> str:
        if not value:
            return "{}"

        lines: list[str] = ["{"]

        for key, item in value.items():
            rendered = self._render_value(item)

            lines.append(
                f"{self._indent(1)}"
                f"{self._render_key(key)} = {rendered}"
            )

        lines.append("}")

        return "\n".join(lines)

    def _render_list(
        self,
        value: list[Any],
        *,
        expression: bool = False,
    ) -> str:
        if not value:
            return "[]"

        rendered_items = [
            self._render_value(
                item,
                expression=expression,
            )
            for item in value
        ]

        return "[" + ", ".join(rendered_items) + "]"

    def _render_key(
        self,
        key: str,
    ) -> str:
        if (
            key
            and key.replace("_", "a").isalnum()
            and not key[0].isdigit()
        ):
            return key

        return json.dumps(key)

    def _block(
        self,
        header: str,
        body: str,
        level: int,
    ) -> str:
        indentation = self._indent(level)

        if not body:
            return f"{indentation}{header} {{}}"

        body = self._indent_block(
            body,
            level,
        )

        return (
            f"{indentation}{header} {{\n"
            f"{body}\n"
            f"{indentation}}}"
        )

    def _indent_block(
        self,
        value: str,
        level: int,
    ) -> str:
        prefix = self._indent(level)

        return "\n".join(
            prefix + line
            for line in value.splitlines()
        )

    def _indent(
        self,
        level: int,
    ) -> str:
        return " " * (self.indent * level)


def generate_terraform(
    project: ProjectIR,
) -> str:
    return TerraformGenerator().generate(project)