# src/iac_converter/ir/expression.py

from dataclasses import dataclass
from typing import Any


class Expression:
    """
    Base class for Terraform expressions.
    """

    pass


@dataclass(frozen=True)
class Literal(Expression):
    value: Any


@dataclass(frozen=True)
class RawExpression(Expression):
    """
    A Terraform expression that we preserve as source text.

    This is useful initially for expressions that our structured
    expression parser does not understand yet.
    """

    value: str