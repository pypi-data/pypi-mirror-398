from __future__ import annotations

from codegen.models import DeferredVar, ImportHelper, PredefinedFn, Program, expr, stmt

from sera.misc import assert_not_null
from sera.models import DataCollection, Module, Package
from sera.typing import GLOBAL_IDENTS


def make_python_create_api(
    collection: DataCollection, target_pkg: Package
) -> tuple[Module, str]:
    """Make an endpoint for creating a resource"""
    app = target_pkg.app

    program = Program()
    import_helper = ImportHelper(program, GLOBAL_IDENTS)

    program.import_("__future__.annotations", True)
    program.import_("litestar.post", True)
    program.import_(
        app.services.path
        + f".{collection.get_pymodule_name()}.{collection.get_service_name()}",
        True,
    )
    program.import_(
        app.models.data.path
        + f".{collection.get_pymodule_name()}.Create{collection.name}",
        True,
    )

    # assuming the collection has only one class
    cls = collection.cls
    is_on_create_update_props = any(
        prop.data.system_controlled is not None
        and prop.data.system_controlled.is_on_create_value_updated()
        for prop in cls.properties.values()
    )
    idprop = assert_not_null(cls.get_id_property())

    if is_on_create_update_props:
        program.import_("sera.libs.api_helper.SingleAutoUSCP", True)

    func_name = "create"

    program.root(
        stmt.LineBreak(),
        stmt.PythonDecoratorStatement(
            expr.ExprFuncCall(
                expr.ExprIdent("post"),
                [
                    expr.ExprConstant("/"),
                ]
                + (
                    [
                        PredefinedFn.keyword_assignment(
                            "dto",
                            PredefinedFn.item_getter(
                                expr.ExprIdent("SingleAutoUSCP"),
                                expr.ExprIdent(f"Create{cls.name}"),
                            ),
                        )
                    ]
                    if is_on_create_update_props
                    else []
                ),
            )
        ),
        lambda ast10: ast10.func(
            func_name,
            [
                DeferredVar.simple(
                    "data",
                    expr.ExprIdent(f"Create{cls.name}"),
                ),
                DeferredVar.simple(
                    "session",
                    import_helper.use("AsyncSession"),
                ),
            ],
            return_type=expr.ExprIdent(idprop.datatype.get_python_type().type),
            is_async=True,
        )(
            stmt.SingleExprStatement(expr.ExprConstant("Creating new record")),
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
            lambda ast13: ast13.return_(
                PredefinedFn.attr_getter(
                    expr.ExprAwait(
                        expr.ExprMethodCall(
                            expr.ExprIdent("service"),
                            "create",
                            [
                                expr.ExprMethodCall(
                                    expr.ExprIdent("data"), "to_db", []
                                ),
                                expr.ExprIdent("session"),
                            ],
                        )
                    ),
                    expr.ExprIdent(idprop.name),
                )
            ),
        ),
    )

    outmod = target_pkg.module("create")
    outmod.write(program)

    return outmod, func_name
