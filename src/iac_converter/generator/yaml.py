from __future__ import annotations

from typing import Any

import yaml

from iac_converter.ir import (
    Block,
    CollectionExpression,
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


class YAMLGenerationError(ValueError):
    """Raised when IR cannot be converted to YAML."""


class YAMLGenerator:
    def generate(self, project: ProjectIR) -> str:
        document: dict[str, Any] = {}

        # Keep the project version as a string and emit it canonically as
        # version: "1" below. This avoids YAML parsers interpreting "1"
        # as an integer and keeps the project format stable.
        document["version"] = str(project.version)

        if project.terraform:
            document["terraform"] = self._convert_value(
                project.terraform
            )

        if project.providers:
            document["providers"] = self._generate_providers(
                project.providers
            )

        if project.variables:
            document["variables"] = [
                self._generate_variable(variable)
                for variable in project.variables
            ]

        if project.locals:
            document["locals"] = self._convert_value(
                project.locals
            )

        if project.data_sources:
            document["data_sources"] = [
                self._generate_data_source(data_source)
                for data_source in project.data_sources
            ]

        if project.resources:
            document["resources"] = [
                self._generate_resource(resource)
                for resource in project.resources
            ]

        if project.outputs:
            document["outputs"] = [
                self._generate_output(output)
                for output in project.outputs
            ]

        # Remove parser-specific metadata immediately before serialization.
        document = self._clean_internal_markers(document)

        result = yaml.safe_dump(
            document,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

        # Keep the project version in its canonical quoted form.
        if result.startswith("version: '1'"):
            result = result.replace(
                "version: '1'",
                'version: "1"',
                1,
            )

        return result

    # ---------------------------------------------------------------
    # Providers
    # ---------------------------------------------------------------

    def _generate_providers(
        self,
        providers: list[Provider],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for provider in providers:
            configuration = self._convert_value(
                provider.configuration
            )

            if provider.alias is not None:
                configuration["alias"] = provider.alias

            result[provider.name] = {
                "properties": configuration,
            }

        return result

    # ---------------------------------------------------------------
    # Variables
    # ---------------------------------------------------------------

    def _generate_variable(
        self,
        variable: Variable,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": variable.name,
        }

        if variable.type is not None:
            result["type"] = self._convert_value(variable.type)

        if variable.description is not None:
            result["description"] = variable.description

        if variable.default is not None:
            result["default"] = self._convert_value(
                variable.default
            )

        if variable.sensitive:
            result["sensitive"] = True

        if variable.nullable is not None:
            result["nullable"] = variable.nullable

        if variable.validation:
            result["validation"] = self._convert_value(
                variable.validation
            )

        return result

    # ---------------------------------------------------------------
    # Resources
    # ---------------------------------------------------------------

    def _generate_resource(
        self,
        resource: Resource,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": resource.type,
            "name": resource.name,
            "properties": self._convert_value(
                resource.attributes
            ),
        }
        if resource.blocks:
            result["blocks"] = [
                self._generate_block(block)
                for block in resource.blocks
            ]

        if resource.count is not None:
            result["count"] = self._convert_value(resource.count)

        if resource.for_each is not None:
            result["for_each"] = self._convert_value(
                resource.for_each
            )

        if resource.depends_on:
            result["depends_on"] = self._convert_value(
                resource.depends_on
            )

        if resource.lifecycle:
            result["lifecycle"] = self._convert_value(
                resource.lifecycle
            )

        if resource.provisioners:
            result["provisioners"] = self._convert_value(
                resource.provisioners
            )

        return result

    def _generate_block(self, block: Block) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": block.type,
            "labels": list(block.labels),
            "properties": self._convert_value(
                block.attributes
            ),
        }

        if block.blocks:
            result["blocks"] = [
                self._generate_block(child)
                for child in block.blocks
            ]

        return result

    # ---------------------------------------------------------------
    # Data sources
    # ---------------------------------------------------------------

    def _generate_data_source(
        self,
        data_source: DataSource,
    ) -> dict[str, Any]:
        return {
            "type": data_source.type,
            "name": data_source.name,
            "properties": self._convert_value(
                data_source.attributes
            ),
        }

    # ---------------------------------------------------------------
    # Outputs
    # ---------------------------------------------------------------

    def _generate_output(
        self,
        output: Output,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": output.name,
            "value": self._convert_value(output.value),
        }

        if output.description is not None:
            result["description"] = output.description

        if output.sensitive:
            result["sensitive"] = True

        if output.depends_on:
            result["depends_on"] = self._convert_value(
                output.depends_on
            )

        return result

    # ---------------------------------------------------------------
    # Values
    # ---------------------------------------------------------------

    def _convert_value(self, value: Any) -> Any:
        if isinstance(value, Literal):
            return self._convert_literal(value.value)

        if isinstance(value, Reference):
            return {
                "reference": {
                    "resource_type": value.resource_type,
                    "resource_name": value.resource_name,
                    **(
                        {"attribute": value.attribute}
                        if value.attribute is not None
                        else {}
                    ),
                }
            }

        if isinstance(value, RawExpression):
            return {
                "expression": value.value,
            }

        if isinstance(value, CollectionExpression):
            if value.kind == "map":
                return {
                    key: self._convert_value(item)
                    for key, item in value.items
                    if key != "__is_block__"
                }

            if value.kind in {"list", "tuple"}:
                return [
                    self._convert_value(item)
                    for item in value.items
                ]

            raise YAMLGenerationError(
                f"Unsupported collection kind: {value.kind}"
            )

        if isinstance(value, dict):
            return {
                key: self._convert_value(item)
                for key, item in value.items()
                if key != "__is_block__"
            }

        if isinstance(value, list):
            return [
                self._convert_value(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                self._convert_value(item)
                for item in value
            ]

        if value is None:
            return None

        return self._convert_literal(value)

    def _convert_literal(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._convert_literal(item)
                for key, item in value.items()
                if key != "__is_block__"
            }

        if isinstance(value, list):
            return [
                self._convert_literal(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                self._convert_literal(item)
                for item in value
            ]

        return value

    def _clean_internal_markers(self, value: Any) -> Any:
        """Remove internal parser metadata recursively."""
        if isinstance(value, dict):
            return {
                key: self._clean_internal_markers(item)
                for key, item in value.items()
                if key != "__is_block__"
            }

        if isinstance(value, list):
            return [
                self._clean_internal_markers(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                self._clean_internal_markers(item)
                for item in value
            ]

        return value


def generate_yaml(project: ProjectIR) -> str:
    return YAMLGenerator().generate(project)


