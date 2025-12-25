from __future__ import annotations

from codegen.models import DeferredVar, ImportHelper, PredefinedFn, Program, expr, stmt

from sera.misc import assert_not_null
from sera.models import DataCollection, Module, Package
from sera.typing import GLOBAL_IDENTS


def make_python_get_by_id_api(
    collection: DataCollection, target_pkg: Package
) -> tuple[Module, str]:
    """Make an endpoint for querying resource by id"""
    app = target_pkg.app

    program = Program()
    import_helper = ImportHelper(program, GLOBAL_IDENTS)

    program.import_("__future__.annotations", True)
    program.import_("litestar.get", True)
    program.import_("litestar.status_codes", True)
    program.import_("litestar.exceptions.HTTPException", True)
    program.import_(
        app.services.path
        + f".{collection.get_pymodule_name()}.{collection.get_service_name()}",
        True,
    )
    program.import_(
        app.models.data.path + f".{collection.get_pymodule_name()}.{collection.name}",
        True,
    )

    # assuming the collection has only one class
    cls = collection.cls
    id_type = assert_not_null(cls.get_id_property()).datatype.get_python_type().type

    func_name = "get_by_id"
    program.root(
        stmt.LineBreak(),
        stmt.PythonDecoratorStatement(
            expr.ExprFuncCall(
                expr.ExprIdent("get"),
                [
                    expr.ExprConstant("/{id:%s}" % id_type),
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
            return_type=expr.ExprIdent("dict"),
            is_async=True,
        )(
            stmt.SingleExprStatement(expr.ExprConstant("Retrieving record by id")),
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
                DeferredVar.simple("record"),
                expr.ExprAwait(
                    expr.ExprFuncCall(
                        expr.ExprIdent("service.get_by_id"),
                        [
                            expr.ExprIdent("id"),
                            expr.ExprIdent("session"),
                        ],
                    )
                ),
            ),
            lambda ast12: ast12.if_(PredefinedFn.is_null(expr.ExprIdent("record")))(
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
            lambda ast13: ast13.return_(
                PredefinedFn.dict(
                    [
                        (
                            PredefinedFn.attr_getter(
                                expr.ExprIdent(cls.name), expr.ExprIdent("__name__")
                            ),
                            PredefinedFn.list(
                                [
                                    expr.ExprFuncCall(
                                        PredefinedFn.attr_getter(
                                            expr.ExprIdent(cls.name),
                                            expr.ExprIdent("from_db"),
                                        ),
                                        [expr.ExprIdent("record")],
                                    )
                                ]
                            ),
                        )
                    ]
                ),
            ),
        ),
    )

    outmod = target_pkg.module("get_by_id")
    outmod.write(program)

    return outmod, func_name
