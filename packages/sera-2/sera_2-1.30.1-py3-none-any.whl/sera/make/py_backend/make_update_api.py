from __future__ import annotations

from codegen.models import DeferredVar, ImportHelper, PredefinedFn, Program, expr, stmt

from sera.misc import assert_not_null
from sera.models import DataCollection, Module, Package
from sera.typing import GLOBAL_IDENTS


def make_python_update_api(
    collection: DataCollection, target_pkg: Package
) -> tuple[Module, str]:
    """Make an endpoint for updating resource"""
    app = target_pkg.app

    program = Program()
    import_helper = ImportHelper(program, GLOBAL_IDENTS)

    program.import_("__future__.annotations", True)
    program.import_("litestar.put", True)
    program.import_(
        app.services.path
        + f".{collection.get_pymodule_name()}.{collection.get_service_name()}",
        True,
    )
    program.import_(
        app.models.data.path
        + f".{collection.get_pymodule_name()}.Update{collection.name}",
        True,
    )

    # assuming the collection has only one class
    cls = collection.cls
    id_prop = assert_not_null(cls.get_id_property())
    id_type = id_prop.datatype.get_python_type().type

    is_on_update_update_props = any(
        prop.data.system_controlled is not None
        and prop.data.system_controlled.is_on_update_value_updated()
        for prop in cls.properties.values()
    )
    if is_on_update_update_props:
        program.import_("sera.libs.api_helper.SingleAutoUSCP", True)

    func_name = "update"

    program.root(
        stmt.LineBreak(),
        stmt.PythonDecoratorStatement(
            expr.ExprFuncCall(
                expr.ExprIdent("put"),
                [
                    expr.ExprConstant("/{id:%s}" % id_type),
                ]
                + (
                    [
                        PredefinedFn.keyword_assignment(
                            "dto",
                            PredefinedFn.item_getter(
                                expr.ExprIdent("SingleAutoUSCP"),
                                expr.ExprIdent(f"Update{cls.name}"),
                            ),
                        )
                    ]
                    if is_on_update_update_props
                    else []
                ),
            )
        ),
        lambda ast10: ast10.func(
            func_name,
            [
                DeferredVar.simple(
                    "id",
                    expr.ExprIdent(id_type),
                ),
                DeferredVar.simple(
                    "data",
                    expr.ExprIdent(f"Update{cls.name}"),
                ),
                DeferredVar.simple(
                    "session",
                    import_helper.use("AsyncSession"),
                ),
            ],
            return_type=expr.ExprIdent(id_prop.datatype.get_python_type().type),
            is_async=True,
        )(
            stmt.SingleExprStatement(expr.ExprConstant("Update an existing record")),
            lambda ast100: ast100.assign(
                DeferredVar.simple("service"),
                expr.ExprFuncCall(
                    PredefinedFn.attr_getter(
                        expr.ExprIdent(collection.get_service_name()),
                        expr.ExprIdent("get_instance"),
                    ),
                    [],
                ),
            ),
            stmt.SingleExprStatement(
                PredefinedFn.attr_setter(
                    expr.ExprIdent("data"),
                    expr.ExprIdent(id_prop.name),
                    expr.ExprIdent("id"),
                )
            ),
            lambda ast13: ast13.return_(
                PredefinedFn.attr_getter(
                    expr.ExprAwait(
                        expr.ExprMethodCall(
                            expr.ExprIdent("service"),
                            "update",
                            [
                                expr.ExprMethodCall(
                                    expr.ExprIdent("data"), "to_db", []
                                ),
                                expr.ExprIdent("session"),
                            ],
                        )
                    ),
                    expr.ExprIdent(id_prop.name),
                )
            ),
        ),
    )

    outmod = target_pkg.module("update")
    outmod.write(program)

    return outmod, func_name
