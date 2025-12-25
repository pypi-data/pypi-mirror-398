from __future__ import annotations

from codegen.models import (
    Program,
    expr,
    stmt,
)

from sera.models import (
    Package,
    Schema,
)
from sera.typing import ObjectPath


def make_python_enums(
    schema: Schema,
    target_pkg: Package,
    reference_objects: dict[str, ObjectPath],
):
    """Make enums defined in the schema.

    Args:
        schema: The schema to generate the classes from.
        target_pkg: The package to write the enums to.
        reference_objects: A dictionary of objects to their references (e.g., the ones that are defined outside and used as referenced such as Tenant).
    """
    for enum in schema.enums.values():
        if enum.name in reference_objects:
            # skip enums that are defined in different apps
            continue

        program = Program()
        program.import_("__future__.annotations", True)
        program.import_("enum.Enum", True)

        enum_values = []
        for value in enum.values.values():
            enum_values.append(
                stmt.DefClassVarStatement(
                    name=value.name,
                    type=None,
                    value=expr.ExprConstant(value.value),
                )
            )

        program.root(
            stmt.LineBreak(),
            lambda ast: ast.class_(
                enum.name,
                (
                    [expr.ExprIdent("str")]
                    if enum.is_str_enum()
                    else [expr.ExprIdent("int")]
                )
                + [expr.ExprIdent("Enum")],
            )(*enum_values),
        )

        target_pkg.module(enum.get_pymodule_name()).write(program)
