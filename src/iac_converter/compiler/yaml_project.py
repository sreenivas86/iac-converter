from __future__ import annotations

from iac_converter.ir import ProjectIR
from iac_converter.parser.yaml_parser import YAMLParseError, parse_yaml


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
