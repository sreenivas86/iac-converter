# src/iac_converter/ir/resource.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Resource:
    """
    A Terraform-managed infrastructure resource.

    Example:

        resource "aws_s3_bucket" "data" {
            bucket = "company-data"
        }
    """

    type: str
    name: str

    attributes: dict[str, Any] = field(default_factory=dict)

    count: Any | None = None

    for_each: Any | None = None

    depends_on: list[Any] = field(default_factory=list)

    lifecycle: dict[str, Any] = field(default_factory=dict)

    provisioners: list[dict[str, Any]] = field(default_factory=list)