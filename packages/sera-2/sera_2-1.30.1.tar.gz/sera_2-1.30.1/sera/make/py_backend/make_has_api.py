from __future__ import annotations

from codegen.models import DeferredVar, ImportHelper, PredefinedFn, Program, expr, stmt

from sera.misc import assert_not_null
from sera.models import DataCollection, Module, Package
from sera.typing import GLOBAL_IDENTS


def make_python_has_api(
    collection: DataCollection, target_pkg: Package
) -> tuple[Module, str]:
    """Make an endpoint for querying resource by id"""
    app = target_pkg.app

    program = Program()
    import_helper = ImportHelper(program, GLOBAL_IDENTS)

    program.import_("__future__.annotations", True)
    program.import_("litestar.head", True)
    program.import_("litestar.status_codes", True)
    program.import_("litestar.exceptions.HTTPException", True)
    program.import_(
        app.services.path
        + f".{collection.get_pymodule_name()}.{collection.get_service_name()}",
        True,
    )

    # assuming the collection has only one class
    cls = collection.cls
    id_type = assert_not_null(cls.get_id_property()).datatype.get_python_type().type

    func_name = "has"
    program.root(
        stmt.LineBreak(),
        stmt.PythonDecoratorStatement(
            expr.ExprFuncCall(
                expr.ExprIdent("head"),
                [
                    expr.ExprConstant("/{id:%s}" % id_type),
                    PredefinedFn.keyword_assignment(
                        "status_code",
                        expr.ExprIdent("status_codes.HTTP_204_NO_CONTENT"),
                    ),
                ],
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
                    "session",
                    import_helper.use("AsyncSession"),
                ),
            ],
            return_type=expr.ExprConstant(None),
            is_async=True,
        )(
            stmt.SingleExprStatement(
                expr.ExprConstant("Checking if record exists by id")
            ),
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
            lambda ast11: ast11.assign(
                DeferredVar.simple("record_exist"),
                expr.ExprAwait(
                    expr.ExprFuncCall(
                        expr.ExprIdent("service.has_id"),
                        [
                            expr.ExprIdent("id"),
                            expr.ExprIdent("session"),
                        ],
                    )
                ),
            ),
            lambda ast12: ast12.if_(expr.ExprNegation(expr.ExprIdent("record_exist")))(
                lambda ast23: ast23.raise_exception(
                    expr.StandardExceptionExpr(
                        expr.ExprIdent("HTTPException"),
                        [
                            PredefinedFn.keyword_assignment(
                                "status_code",
                                expr.ExprIdent("status_codes.HTTP_404_NOT_FOUND"),
                            ),
                            PredefinedFn.keyword_assignment(
                                "detail",
                                expr.ExprIdent('f"Record with id {id} not found"'),
                            ),
                        ],
                    )
                )
            ),
            lambda ast13: ast13.return_(expr.ExprConstant(None)),
        ),
    )

    outmod = target_pkg.module("has")
    outmod.write(program)

    return outmod, func_name
