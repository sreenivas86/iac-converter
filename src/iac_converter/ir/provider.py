# src/iac_converter/ir/provider.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Provider:
    """
    Terraform provider configuration.

    Example:

        provider "aws" {
            region = "ap-south-1"
        }
    """

    name: str

    alias: str | None = None

    configuration: dict[str, Any] = field(default_factory=dict)