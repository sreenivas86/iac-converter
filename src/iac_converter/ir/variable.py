# src/iac_converter/ir/variable.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Variable:
    name: str

    type: Any | None = None

    description: str | None = None

    default: Any | None = None

    sensitive: bool = False

    nullable: bool | None = None

    validation: list[dict[str, Any]] = field(default_factory=list)
