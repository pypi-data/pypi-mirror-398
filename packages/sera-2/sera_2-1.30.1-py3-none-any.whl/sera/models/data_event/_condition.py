from __future__ import annotations

from dataclasses import dataclass, field

from sera.models._expression import Expr


@dataclass
class EventCondition:
    """Represents a condition in Conjunctive Normal Form (CNF).

    CNF is represented as a list of OR clauses, where all must be true (AND).
    Each OR clause is a list of EventClause where at least one must be true.

    Example CNF:
    - [[A], [B, C]] represents: A AND (B OR C)
    - [[A, B]] represents: (A OR B)
    - [[A], [B], [C]] represents: A AND B AND C
    """

    # List of OR clauses (each OR clause is a list of EventClause)
    # All OR clauses must evaluate to true (AND relationship)
    clauses: list[list[Expr]] = field(default_factory=list)
