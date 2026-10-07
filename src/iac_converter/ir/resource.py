
from dataclasses import dataclass, field
from typing import Any

from iac_converter.ir.block import Block


@dataclass
class Resource:
    type: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
    count: Any | None = None
    for_each: Any | None = None
    depends_on: list[Any] = field(default_factory=list)
    lifecycle: dict[str, Any] = field(default_factory=dict)
    provisioners: list[dict[str, Any]] = field(default_factory=list)
