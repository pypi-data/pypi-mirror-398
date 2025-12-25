from __future__ import annotations

from dataclasses import dataclass

from codegen.models import AST, expr

from sera.models._expression import Expr
from sera.models._property import Property


@dataclass
class EventAction:
    """Represents an action to perform when event conditions are met."""

    pass


@dataclass
class AssignValueAction(EventAction):
    """Set a field to a specific value."""

    property: Property
    value: Expr


@dataclass
class FunctionCallAction(EventAction):
    """Call a function with arguments."""

    func_name: str
    args: dict[str, Expr]
