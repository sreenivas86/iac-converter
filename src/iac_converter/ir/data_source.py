# src/iac_converter/ir/data_source.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DataSource:
    """
    Terraform data source.

    Example:

        data "aws_caller_identity" "current" {}
    """

    type: str

    name: str

    attributes: dict[str, Any] = field(default_factory=dict)

    depends_on: list[Any] = field(default_factory=list)
