from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Block:
    type: str
    labels: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
