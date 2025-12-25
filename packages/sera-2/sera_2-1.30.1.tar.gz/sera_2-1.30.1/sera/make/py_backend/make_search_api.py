from __future__ import annotations

from codegen.models import DeferredVar, ImportHelper, PredefinedFn, Program, expr, stmt
from sqlalchemy.event import attr

from sera.make.py_backend.misc import get_python_property_name
from sera.models import DataCollection, Module, Package
from sera.models._property import DataProperty, ObjectProperty
from sera.typing import GLOBAL_IDENTS


def make_python_search_api(
    collection: DataCollection, target_pkg: Package
) -> tuple[Module, str]:
    """Make an endpoint for querying resources"""
    app = target_pkg.app

    program = Program()
    import_helper = ImportHelper(program, GLOBAL_IDENTS)

    program.import_("__future__.annotations", True)
    program.import_("litestar.post", True)
    program.import_(app.config.path + ".schema", True)
    program.import_(app.config.path + ".API_DEBUG", True)
    program.import_(
        app.services.path
        + f".{collection.get_pymodule_name()}.{collection.get_service_name()}",
        True,
    )
    program.import_(
        app.models.path + ".data_schema.dataschema",
        True,
    )
    program.import_("sera.libs.search_helper.Query", True)
    program.import_("sera.libs.search_helper.AllowedFields", True)

    search_controlled_props = [
        prop
        for prop in collection.cls.properties.values()
        if prop.data.system_controlled is not None
        and prop.data.system_controlled.is_on_search_value_updated()
    ]
    if len(search_controlled_props) > 0:
        program.import_(
            "sera.libs.api_helper.SKIP_UPDATE_SYSTEM_CONTROLLED_PROPS_KEY", True
        )
        program.import_("litestar.types.Scope", True)

    func_name = "search"

    program.root(
        stmt.LineBreak(),
        lambda ast: ast.assign(
            DeferredVar.simple("QUERYABLE_FIELDS"),
            expr.ExprNewInstance(
                expr.ExprIdent("AllowedFields"),
                [
                    PredefinedFn.set(
                        [
                            expr.ExprConstant(
                                get_python_property_name(prop)
                                if isinstance(prop, (DataProperty, ObjectProperty))
                                else tuple(
                                    get_python_property_name(_prop) for _prop in prop
                                )
                            )
                            for prop in collection.get_queryable_fields()
                        ]
                    )
                ],
            ),
        ),
        stmt.LineBreak(),
        lambda ast: ast.assign(
            DeferredVar.simple("JOIN_QUERYABLE_FIELDS"),
            PredefinedFn.dict(
                [
                    (
                        expr.ExprConstant(propname),
                        PredefinedFn.set(
                            [
                                expr.ExprConstant(get_python_property_name(f))
                                for f in fields
                            ]
                        ),
                    )
                    for propname, fields in collection.get_join_queryable_fields().items()
                ]
            ),
        ),
        stmt.LineBreak(),
        stmt.PythonDecoratorStatement(
            expr.ExprFuncCall(
                expr.ExprIdent("post"),
                [
                    expr.ExprConstant("/q"),
                ],
            )
        ),
        lambda ast10: ast10.func(
            func_name,
            [
                DeferredVar.simple(
                    "data",
                    expr.ExprIdent("Query"),
                ),
                DeferredVar.simple(
                    "session",
                    import_helper.use("AsyncSession"),
                ),
            ]
            + (
                [DeferredVar.simple("scope", expr.ExprIdent("Scope"))]
                if len(search_controlled_props) > 0
                else []
            ),
            return_type=expr.ExprIdent("dict"),
            is_async=True,
        )(
            stmt.SingleExprStatement(
                expr.ExprConstant("Retrieving records matched a query")
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
            (
                stmt.SingleExprStatement(
                    expr.ExprFuncCall(
                        PredefinedFn.attr_getter(
                            expr.ExprIdent("data"),
                            expr.ExprIdent("inject_controlled_fields"),
                        ),
                        [
                            PredefinedFn.dict(
                                [
                                    (
                                        expr.ExprConstant(
                                            get_python_property_name(prop)
                                        ),
                                        PredefinedFn.attr_getter(
                                            PredefinedFn.item_getter(
                                                expr.ExprIdent("scope"),
                                                expr.ExprConstant("user"),
                                            ),
                                            expr.ExprIdent(
                                                get_python_property_name(prop)
                                            ),
                                        ),
                                    )
                                    for prop in search_controlled_props
                                ]
                            ),
                            expr.ExprNegation(
                                PredefinedFn.item_getter(
                                    PredefinedFn.item_getter(
                                        expr.ExprIdent("scope"),
                                        expr.ExprConstant("state"),
                                    ),
                                    expr.ExprIdent(
                                        "SKIP_UPDATE_SYSTEM_CONTROLLED_PROPS_KEY"
                                    ),
                                )
                            ),
                        ],
                    )
                )
                if len(search_controlled_props) > 0
                else None
            ),
            stmt.SingleExprStatement(
                expr.ExprFuncCall(
                    PredefinedFn.attr_getter(
                        expr.ExprIdent("data"),
                        expr.ExprIdent("validate_and_normalize"),
                    ),
                    [
                        PredefinedFn.item_getter(
                            PredefinedFn.attr_getter(
                                expr.ExprIdent("schema"), expr.ExprIdent("classes")
                            ),
                            expr.ExprConstant(collection.cls.name),
                        ),
                        expr.ExprIdent("QUERYABLE_FIELDS"),
                        expr.ExprIdent("JOIN_QUERYABLE_FIELDS"),
                        PredefinedFn.keyword_assignment(
                            "debug",
                            expr.ExprIdent("API_DEBUG"),
                        ),
                    ],
                )
            ),
            lambda ast102: ast102.assign(
                DeferredVar.simple("result"),
                expr.ExprAwait(
                    expr.ExprFuncCall(
                        PredefinedFn.attr_getter(
                            expr.ExprIdent("service"),
                            expr.ExprIdent("search"),
                        ),
                        [expr.ExprIdent("data"), expr.ExprIdent("session")],
                    )
                ),
            ),
            lambda ast103: ast103.return_(
                expr.ExprFuncCall(
                    PredefinedFn.attr_getter(
                        expr.ExprIdent("data"),
                        expr.ExprIdent("prepare_results"),
                    ),
                    [
                        PredefinedFn.item_getter(
                            PredefinedFn.attr_getter(
                                expr.ExprIdent("schema"), expr.ExprIdent("classes")
                            ),
                            expr.ExprConstant(collection.cls.name),
                        ),
                        expr.ExprIdent("dataschema"),
                        expr.ExprIdent("result"),
                    ],
                )
            ),
        ),
    )

    outmod = target_pkg.module("search")
    outmod.write(program)

    return outmod, func_name
