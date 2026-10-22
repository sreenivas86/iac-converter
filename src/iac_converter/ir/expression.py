from dataclasses import dataclass, field
from typing import Any


class Expression:
    """Base class for Terraform expressions."""

    pass


@dataclass(frozen=True)
class Literal(Expression):
    """A literal value, such as a string, number, boolean, or null."""

    value: Any


@dataclass(frozen=True)
class RawExpression(Expression):
    """
    A Terraform expression preserved as source text.

    Use this as a fallback when the structured expression parser does not
    understand an expression yet.
    """

    value: str


@dataclass(frozen=True)
class FunctionCall(Expression):
    """A Terraform function call, such as file("userdata.sh")."""

    name: str
    arguments: tuple[Expression, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConditionalExpression(Expression):
    """A Terraform conditional expression: condition ? true_value : false_value."""

    condition: Expression
    true_value: Expression
    false_value: Expression


@dataclass(frozen=True)
class CollectionExpression(Expression):
    """
    A structured Terraform collection expression.

    `kind` should be "list", "tuple", or "map".
    Lists and tuples use `items`; maps use `items` as key/value pairs.
    """

    kind: str
    items: tuple[Any, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.kind not in {"list", "tuple", "map"}:
            raise ValueError(
                "CollectionExpression kind must be 'list', 'tuple', or 'map'."
            )

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)

    def __iter__(self):
        if self.kind == "map":
            return iter(key for key, _ in self.items)
        return iter(self.items)

    def __getitem__(self, key: Any) -> Any:
        if self.kind == "map":
            return dict(self.items)[key]
        return self.items[key]
