from dataclasses import dataclass, field
from typing import Any


@dataclass
class Module:
    """Terraform module call representation."""

    name: str
    source: str
    arguments: dict[str, Any] = field(default_factory=dict)
    count: Any | None = None
    for_each: Any | None = None
    depends_on: list[Any] = field(default_factory=list)
