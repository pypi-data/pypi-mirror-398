from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from sera.models._expression import Expr
from sera.models.data_event import (
    AssignValueAction,
    DataEvent,
    EventAction,
    EventCondition,
    FunctionCallAction,
)
from sera.models.parse.parse_expr import (
    ExprParseError,
    parse_assignment_expression,
    parse_expression,
)

if TYPE_CHECKING:
    from sera.models._property import Property


def parse_data_event(event: dict, properties: Mapping[str, Property]) -> DataEvent:
    """Parse a data event from YAML dictionary.

    Args:
        event: Event definition dictionary
        properties: Dictionary mapping property names to Property objects

    Expected format with natural expressions:
    {
        "when": "type == 'NoVAT'",  # Single condition
        "then": [
            "value = 0",  # Assignment action
            "clear_data()",  # Function call action
        ]
    }

    Or with CNF (OR clauses):
    {
        "when": [
            "status == 'active'",  # AND
            ["type == 'A'", "type == 'B'"]  # OR clause
        ],
        "then": ["value = 1", "reset()"]
    }
    """
    if not isinstance(event, dict):
        raise ValueError(f"Event must be a dictionary, got: {type(event)}")

    if "when" not in event:
        raise ValueError("Event must have 'when' clause")
    if "then" not in event:
        raise ValueError("Event must have 'then' clause")

    # Parse condition (CNF)
    when_clauses = event["when"]

    # Convert to list if it's a single string
    if isinstance(when_clauses, str):
        when_clauses = [when_clauses]

    if not isinstance(when_clauses, list):
        raise ValueError(
            f"Event 'when' must be a string or list, got: {type(when_clauses)}"
        )

    # Parse CNF clauses
    cnf_clauses: list[list[Expr]] = []
    for clause_item in when_clauses:
        if isinstance(clause_item, str):
            # Single natural language expression - parse it
            expr = parse_expression(clause_item, properties)
            cnf_clauses.append([expr])
        elif isinstance(clause_item, list):
            # OR clause (list of natural language expressions)
            or_clause = [parse_expression(c, properties) for c in clause_item]
            cnf_clauses.append(or_clause)
        else:
            raise ValueError(f"Invalid clause format: {clause_item}")

    condition = EventCondition(clauses=cnf_clauses)

    # Parse actions
    then_actions = event["then"]
    if not isinstance(then_actions, list):
        raise ValueError(f"Event 'then' must be a list, got: {type(then_actions)}")

    actions = [parse_event_action(action, properties) for action in then_actions]

    return DataEvent(when=condition, then=actions)


def parse_event_action(action: str, properties: Mapping[str, Property]) -> EventAction:
    """Parse a single event action from a string.

    Args:
        action: Action string (e.g., "value = 0", "clear(value)")
        properties: Dictionary mapping property names to Property objects

    Returns:
        EventAction (either AssignValueAction or FunctionCallAction)

    Formats:
        Assignment: "value = 0" or "status = get_status()"
        Function call: "clear_field(value)" or "reset()"

    The parser automatically detects the action type:
    - If the string contains '=', it's treated as an assignment (AssignValueAction)
    - Otherwise, it's treated as a function call (FunctionCallAction)
    """
    if not isinstance(action, str):
        raise ValueError(f"Event action must be a string, got: {type(action)}")

    action = action.strip()

    # Check if it's an assignment (contains '=' but not in comparison context)
    # We use parse_assignment_expression which will fail if it's not a valid assignment
    try:
        field_name, value_expr = parse_assignment_expression(action, properties)

        if field_name not in properties:
            raise ValueError(
                f"Unknown property '{field_name}' in action. "
                f"Available: {list(properties.keys())}"
            )

        return AssignValueAction(
            property=properties[field_name],
            value=value_expr,
        )
    except ExprParseError as assignment_error:
        # If assignment parsing fails, try parsing as a function call
        try:
            # Parse as a function call expression
            func_expr = parse_expression(action, properties)

            # Ensure it's actually a function call
            from sera.models._expression import FuncCallExpr

            if not isinstance(func_expr, FuncCallExpr):
                raise ValueError(
                    f"Action must be either an assignment (field = value) or "
                    f"a function call (func(args)), got: {action}"
                )

            # Convert FuncCallExpr to FunctionCallAction
            # Convert positional args and kwargs to a single dict
            args_dict: dict[str, Expr] = {}

            # Add positional args with numeric keys
            for i, arg in enumerate(func_expr.args):
                args_dict[str(i)] = arg

            # Add keyword args
            if func_expr.kwargs:
                args_dict.update(func_expr.kwargs)

            return FunctionCallAction(
                func_name=func_expr.func_name,
                args=args_dict,
            )
        except Exception as func_error:
            # Neither assignment nor function call worked
            raise ValueError(
                f"Failed to parse action '{action}'. "
                f"Assignment error: {assignment_error}. "
                f"Function call error: {func_error}"
            )
