"""Expression classes for building complex expressions in SERA models.

This module provides a hierarchy of expression classes that can be used to represent
various types of expressions including constants, property references, boolean operations,
function calls, and arithmetic operations.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sera.models._property import Property


class Expr(ABC):
    """Base class for all expression types."""


@dataclass
class ConstantExpr(Expr):
    """Expression representing a constant value.

    Attributes:
        value: The constant value (can be str, int, float, bool, None, etc.)
    """

    value: Optional[str | int | float | bool | tuple[str, ...]]


@dataclass
class AttrGetterExpr(Expr):
    """Expression representing a property reference.

    Attributes:
        property: The Property instance being referenced
    """

    property: Property


class BoolOp(str, Enum):
    """Boolean operator types."""

    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class LogicalExpr(Expr):
    """Expression representing a boolean operation.

    Attributes:
        operator: The boolean operator (AND, OR, NOT)
        operands: List of operand expressions
    """

    operator: BoolOp
    operands: list[Expr]

    def __post_init__(self):
        """Validate operands based on operator type."""
        if self.operator == BoolOp.NOT and len(self.operands) != 1:
            raise ValueError("NOT operator requires exactly one operand")
        if self.operator in (BoolOp.AND, BoolOp.OR):
            if len(self.operands) < 2:
                raise ValueError(
                    f"{self.operator.value.upper()} operator requires at least two operands"
                )


class ArithmeticOp(str, Enum):
    """Arithmetic operator types."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    POWER = "**"


# Comparison operators - common enough to warrant their own class
class ComparisonOp(str, Enum):
    """Comparison operator types."""

    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "in"
    NOT_IN = "not in"
    IS = "is"
    IS_NOT = "is not"


@dataclass
class BinaryExpr(Expr):
    """Expression representing a binary operation (arithmetic or comparison).

    Attributes:
        operator: The binary operator (arithmetic or comparison)
        left: Left operand expression
        right: Right operand expression
    """

    operator: ArithmeticOp | ComparisonOp
    left: Expr
    right: Expr


@dataclass
class FuncCallExpr(Expr):
    """Expression representing a function call.

    Attributes:
        func_name: The name of the function to call
        args: List of argument expressions
        kwargs: Optional keyword arguments as expressions
    """

    func_name: str
    args: list[Expr]
    kwargs: dict[str, Expr] | None = None


__all__ = [
    "Expr",
    "ConstantExpr",
    "AttrGetterExpr",
    "LogicalExpr",
    "BoolOp",
    "BinaryExpr",
    "ArithmeticOp",
    "FuncCallExpr",
    "ComparisonOp",
]
