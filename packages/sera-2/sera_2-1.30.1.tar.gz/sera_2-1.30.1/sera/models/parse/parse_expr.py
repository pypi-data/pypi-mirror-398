"""Natural expression parser for SERA events.

This module parses natural Python-like expressions into SERA Expr objects using
Python's ast module. Supports comparison, arithmetic, logical operators, function
calls, and property references.

Example:
    type == 'NoVAT'  ->  BinaryExpr(ComparisonOp.EQ, AttrGetterExpr(type), ConstantExpr('NoVAT'))
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Mapping

from sera.models._expression import (
    ArithmeticOp,
    AttrGetterExpr,
    BinaryExpr,
    BoolOp,
    ComparisonOp,
    ConstantExpr,
    Expr,
    FuncCallExpr,
    LogicalExpr,
)

if TYPE_CHECKING:
    from sera.models._property import Property


class ExprParseError(Exception):
    """Exception raised when expression parsing fails."""

    pass


def parse_expression(text: str, properties: Mapping[str, Property]) -> Expr:
    """Parse natural expression like 'age >= 18' into Expr object.

    Args:
        text: The expression string to parse (e.g., "type == 'NoVAT'")
        properties: Dictionary mapping property names to Property objects

    Returns:
        Parsed Expr object

    Raises:
        ExprParseError: If the expression cannot be parsed

    Examples:
        >>> parse_expression("age >= 18", props)
        BinaryExpr(operator=ComparisonOp.GTE, left=AttrGetterExpr(...), right=ConstantExpr(18))

        >>> parse_expression("status == 'active' and score > 50", props)
        LogicalExpr(operator=BoolOp.AND, operands=[...])
    """
    try:
        tree = ast.parse(text.strip(), mode="eval")
        return _convert_ast_to_expr(tree.body, properties)
    except SyntaxError as e:
        raise ExprParseError(f"Invalid Python expression: {text}") from e
    except Exception as e:
        raise ExprParseError(f"Failed to parse expression '{text}': {e}") from e


def parse_assignment_expression(
    text: str, properties: Mapping[str, Property]
) -> tuple[str, Expr]:
    """Parse assignment like 'value = 0' into (field_name, value_expr).

    Args:
        text: The assignment expression string (e.g., "value = 0")
        properties: Dictionary mapping property names to Property objects

    Returns:
        Tuple of (field_name, value_expression)

    Raises:
        ExprParseError: If the expression is not a valid assignment

    Examples:
        >>> parse_assignment_expression("value = 0", props)
        ('value', ConstantExpr(0))

        >>> parse_assignment_expression("status = get_status()", props)
        ('status', FuncCallExpr(...))
    """
    try:
        tree = ast.parse(text.strip(), mode="exec")

        # Should have exactly one statement
        if len(tree.body) != 1:
            raise ExprParseError("Assignment expression must be a single statement")

        stmt = tree.body[0]
        if not isinstance(stmt, ast.Assign):
            raise ExprParseError("Expression must be an assignment (field = value)")

        # Should have exactly one target
        if len(stmt.targets) != 1:
            raise ExprParseError("Assignment must have exactly one target")

        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            raise ExprParseError("Assignment target must be a simple name")

        field_name = target.id
        value_expr = _convert_ast_to_expr(stmt.value, properties)

        return field_name, value_expr

    except SyntaxError as e:
        raise ExprParseError(f"Invalid Python assignment: {text}") from e
    except ExprParseError:
        raise
    except Exception as e:
        raise ExprParseError(f"Failed to parse assignment '{text}': {e}") from e


def _convert_ast_to_expr(node: ast.expr, properties: Mapping[str, Property]) -> Expr:
    """Convert AST node to SERA Expr object.

    Args:
        node: AST expression node
        properties: Dictionary mapping property names to Property objects

    Returns:
        Corresponding Expr object

    Raises:
        ExprParseError: If the node type is not supported
    """
    # Constant values (numbers, strings, booleans, None)
    if isinstance(node, ast.Constant):
        value = node.value
        # Validate that the constant is a supported type
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise ExprParseError(f"Unsupported constant type: {type(value).__name__}")
        return ConstantExpr(value=value)

    # Property references (field names)
    if isinstance(node, ast.Name):
        prop_name = node.id
        if prop_name not in properties:
            raise ExprParseError(
                f"Unknown property '{prop_name}'. Available: {list(properties.keys())}"
            )
        return AttrGetterExpr(property=properties[prop_name])

    # Attribute access (Class.field_name)
    if isinstance(node, ast.Attribute):
        # For now, just support simple attribute access on Name nodes
        if isinstance(node.value, ast.Name):
            # Try the full qualified name first
            qualified_name = f"{node.value.id}.{node.attr}"
            if qualified_name in properties:
                return AttrGetterExpr(property=properties[qualified_name])
            # Fall back to just the attribute name
            if node.attr in properties:
                return AttrGetterExpr(property=properties[node.attr])
            raise ExprParseError(
                f"Unknown property '{qualified_name}' or '{node.attr}'"
            )
        raise ExprParseError(f"Unsupported attribute access: {ast.unparse(node)}")

    # Comparison operations (==, !=, >, >=, <, <=, in, not in, is, is not)
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise ExprParseError("Only simple binary comparisons are supported")

        op = node.ops[0]
        left = _convert_ast_to_expr(node.left, properties)
        right = _convert_ast_to_expr(node.comparators[0], properties)

        # Map AST comparison operators to ComparisonOp
        comparison_op_map: dict[type, ComparisonOp] = {
            ast.Eq: ComparisonOp.EQ,
            ast.NotEq: ComparisonOp.NEQ,
            ast.Gt: ComparisonOp.GT,
            ast.GtE: ComparisonOp.GTE,
            ast.Lt: ComparisonOp.LT,
            ast.LtE: ComparisonOp.LTE,
            ast.In: ComparisonOp.IN,
            ast.NotIn: ComparisonOp.NOT_IN,
            ast.Is: ComparisonOp.IS,
            ast.IsNot: ComparisonOp.IS_NOT,
        }

        comparison_op = comparison_op_map.get(type(op))
        if comparison_op is None:
            raise ExprParseError(f"Unsupported comparison operator: {type(op)}")

        return BinaryExpr(operator=comparison_op, left=left, right=right)

    # Binary arithmetic operations (+, -, *, /, %, **)
    if isinstance(node, ast.BinOp):
        left = _convert_ast_to_expr(node.left, properties)
        right = _convert_ast_to_expr(node.right, properties)

        # Map AST binary operators to ArithmeticOp
        arithmetic_op_map: dict[type, ArithmeticOp] = {
            ast.Add: ArithmeticOp.ADD,
            ast.Sub: ArithmeticOp.SUBTRACT,
            ast.Mult: ArithmeticOp.MULTIPLY,
            ast.Div: ArithmeticOp.DIVIDE,
            ast.Mod: ArithmeticOp.MODULO,
            ast.Pow: ArithmeticOp.POWER,
        }

        arithmetic_op = arithmetic_op_map.get(type(node.op))
        if arithmetic_op is None:
            raise ExprParseError(f"Unsupported arithmetic operator: {type(node.op)}")

        return BinaryExpr(operator=arithmetic_op, left=left, right=right)

    # Boolean operations (and, or, not)
    if isinstance(node, ast.BoolOp):
        operator = BoolOp.AND if isinstance(node.op, ast.And) else BoolOp.OR
        operands = [_convert_ast_to_expr(value, properties) for value in node.values]
        return LogicalExpr(operator=operator, operands=operands)

    # Unary operations (not)
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            operand = _convert_ast_to_expr(node.operand, properties)
            return LogicalExpr(operator=BoolOp.NOT, operands=[operand])
        raise ExprParseError(f"Unsupported unary operator: {type(node.op)}")

    # Function calls
    if isinstance(node, ast.Call):
        # Function name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        else:
            raise ExprParseError(
                f"Only simple function names are supported, got: {ast.unparse(node.func)}"
            )

        # Positional arguments
        args = [_convert_ast_to_expr(arg, properties) for arg in node.args]

        # Keyword arguments
        kwargs = None
        if node.keywords:
            kwargs = {
                kw.arg: _convert_ast_to_expr(kw.value, properties)
                for kw in node.keywords
                if kw.arg is not None  # Skip **kwargs
            }

        return FuncCallExpr(func_name=func_name, args=args, kwargs=kwargs)

    # Lists and tuples (as constant collections)
    if isinstance(node, (ast.List, ast.Tuple)):
        # Convert to tuple of values if all elements are constants
        elements = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant):
                elements.append(elt.value)
            else:
                raise ExprParseError(
                    "Only constant values are supported in list/tuple literals"
                )
        return ConstantExpr(value=tuple(elements))

    raise ExprParseError(f"Unsupported expression type: {type(node).__name__}")


__all__ = [
    "parse_expression",
    "parse_assignment_expression",
    "ExprParseError",
]
