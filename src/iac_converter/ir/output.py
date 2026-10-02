# src/iac_converter/ir/output.py

from dataclasses import dataclass
from typing import Any


@dataclass
class Output:
    name: str

    value: Any

    description: str | None = None

    sensitive: bool = False

    depends_on: list[Any] | None = None