from dataclasses import dataclass
from typing import Any

from .specs import FieldSpec


@dataclass(frozen=True)
class Expr:
    def __and__(self, other: "Expr") -> "And":
        return And(self, other)

    def __or__(self, other: "Expr") -> "Or":
        return Or(self, other)

    def __invert__(self) -> "Not":
        return Not(self)


@dataclass(frozen=True)
class Term(Expr):
    field: FieldSpec
    op: str
    value: Any


@dataclass(frozen=True)
class And(Expr):
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Or(Expr):
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Not(Expr):
    expr: Expr
