# src/iac_converter/ir/model.py

from dataclasses import dataclass, field
from typing import Any

from iac_converter.diagnostics import Diagnostic

from .data_source import DataSource
from .module import Module
from .output import Output
from .provider import Provider
from .resource import Resource
from .variable import Variable


@dataclass
class ProjectIR:
    """
    Canonical intermediate representation of an IaC project.

    This model is intentionally independent of YAML and Terraform.
    """

    version: str = "1"

    providers: list[Provider] = field(default_factory=list)

    variables: list[Variable] = field(default_factory=list)

    resources: list[Resource] = field(default_factory=list)

    data_sources: list[DataSource] = field(default_factory=list)

    outputs: list[Output] = field(default_factory=list)

    modules: list[Module] = field(default_factory=list)

    locals: dict[str, Any] = field(default_factory=dict)

    terraform: dict[str, Any] = field(default_factory=dict)

    diagnostics: list[Diagnostic] = field(default_factory=list)
