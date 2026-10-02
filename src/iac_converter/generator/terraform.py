from __future__ import annotations

import json
from typing import Any

from iac_converter.ir import (
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

        return "\n\n".join(section for section in sections if section.strip()) + "\n"

    # ------------------------------------------------------------------
    # Top-level blocks
    # ------------------------------------------------------------------

    def _terraform_block(self, configuration: dict[str, Any]) -> str:
        body = self._render_arguments(configuration, level=1)

        return self._block(
            header="terraform",
            body=body,
            level=0,
        )

    def _provider_block(self, provider: Provider) -> str:
        arguments = dict(provider.configuration)

        if provider.alias is not None:
            arguments["alias"] = provider.alias

        body = self._render_arguments(arguments, level=1)

        return self._block(
            header=f'provider "{provider.name}"',
            body=body,
            level=0,
        )

    def _variable_block(self, variable: Variable) -> str:
        arguments: list[tuple[str, Any]] = []

        if variable.type is not None:
            arguments.append(("type", variable.type))

        if variable.description is not None:
            arguments.append(("description", variable.description))

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

    def _locals_block(self, locals_values: dict[str, Any]) -> str:
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

    def _data_source_block(self, data_source: DataSource) -> str:
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

    def _resource_block(self, resource: Resource) -> str:
        lines: list[str] = []

        lines.extend(
            self._render_arguments(
                resource.attributes,
                level=1,
            ).splitlines()
        )

        if resource.count is not None:
            lines.extend(
                self._render_argument(
                    "count",
                    resource.count,
                    level=1,
                    expression=True,
                ).splitlines()
            )

        if resource.for_each is not None:
            lines.extend(
                self._render_argument(
                    "for_each",
                    resource.for_each,
                    level=1,
                    expression=True,
                ).splitlines()
            )

        if resource.depends_on:
            lines.extend(
                self._render_argument(
                    "depends_on",
                    resource.depends_on,
                    level=1,
                ).splitlines()
            )

        if resource.lifecycle:
            lines.append(
                self._render_nested_block(
                    "lifecycle",
                    resource.lifecycle,
                    level=1,
                )
            )

        body = "\n".join(line for line in lines if line)

        return self._block(
            header=f'resource "{resource.type}" "{resource.name}"',
            body=body,
            level=0,
        )

    def _output_block(self, output: Output) -> str:
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

        if isinstance(value, Reference):
            return value.to_string()

        if isinstance(value, RawExpression):
            return value.value

        if isinstance(value, dict):
            return self._render_object(value)

        if isinstance(value, list):
            return self._render_list(value)

        if isinstance(value, tuple):
            return self._render_list(list(value))

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
            return self._render_list(value)

        raise TerraformGenerationError(
            f"Unsupported literal type: {type(value).__name__}"
        )

    def _render_object(self, value: dict[str, Any]) -> str:
        if not value:
            return "{}"

        lines: list[str] = ["{"]

        for key, item in value.items():
            rendered = self._render_value(item)

            lines.append(
                f"{self._indent(1)}{self._render_key(key)} = {rendered}"
            )

        lines.append("}")

        return "\n".join(lines)

    def _render_list(self, value: list[Any]) -> str:
        if not value:
            return "[]"

        rendered_items = [
            self._render_value(item)
            for item in value
        ]

        return "[" + ", ".join(rendered_items) + "]"

    def _render_key(self, key: str) -> str:
        if key.replace("_", "a").isalnum() and not key[0].isdigit():
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

        body = self._indent_block(body, level)

        return (
            f"{indentation}{header} {{\n"
            f"{body}\n"
            f"{indentation}}}"
        )

    def _indent_block(self, value: str, level: int) -> str:
        prefix = self._indent(level)

        return "\n".join(
            prefix + line
            for line in value.splitlines()
        )

    def _indent(self, level: int) -> str:
        return " " * (self.indent * level)


def generate_terraform(project: ProjectIR) -> str:
    return TerraformGenerator().generate(project)