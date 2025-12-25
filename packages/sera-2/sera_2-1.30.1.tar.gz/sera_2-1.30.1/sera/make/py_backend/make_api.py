from __future__ import annotations

from typing import Sequence

from codegen.models import DeferredVar, PredefinedFn, Program, expr, stmt
from loguru import logger

from sera.make.py_backend.make_create_api import make_python_create_api
from sera.make.py_backend.make_get_by_id_api import make_python_get_by_id_api
from sera.make.py_backend.make_has_api import make_python_has_api
from sera.make.py_backend.make_search_api import make_python_search_api
from sera.make.py_backend.make_update_api import make_python_update_api
from sera.misc import to_snake_case
from sera.models import App, DataCollection, Module, Package


def make_python_api(app: App, collections: Sequence[DataCollection]):
    """Make the basic structure for the API."""
    app.api.ensure_exists()
    app.api.pkg("routes").ensure_exists()

    # make routes
    routes: list[Module] = []
    for collection in collections:
        route = app.api.pkg("routes").pkg(collection.get_pymodule_name())

        controllers = []
        controllers.append(make_python_search_api(collection, route))
        controllers.append(make_python_get_by_id_api(collection, route))
        controllers.append(make_python_has_api(collection, route))
        controllers.append(make_python_create_api(collection, route))
        controllers.append(make_python_update_api(collection, route))

        routemod = route.module("route")
        if not routemod.exists():
            program = Program()
            program.import_("__future__.annotations", True)
            program.import_("litestar.Router", True)
            for get_route, get_route_fn in controllers:
                program.import_(get_route.path + "." + get_route_fn, True)

            program.root(
                stmt.LineBreak(),
                lambda ast: ast.assign(
                    DeferredVar.simple("router"),
                    expr.ExprFuncCall(
                        expr.ExprIdent("Router"),
                        [
                            PredefinedFn.keyword_assignment(
                                "path",
                                expr.ExprConstant(
                                    f"/api/{to_snake_case(collection.name).replace('_', '-')}"
                                ),
                            ),
                            PredefinedFn.keyword_assignment(
                                "route_handlers",
                                PredefinedFn.list(
                                    [
                                        expr.ExprIdent(get_route_fn)
                                        for get_route, get_route_fn in controllers
                                    ]
                                ),
                            ),
                            PredefinedFn.keyword_assignment(
                                "tags",
                                PredefinedFn.list(
                                    [expr.ExprConstant(collection.get_pymodule_name())]
                                ),
                            ),
                        ],
                    ),
                ),
            )

            routemod.write(program)
        routes.append(routemod)

    # make the main entry point
    make_main(app.api, routes)


def make_main(target_pkg: Package, routes: Sequence[Module]):
    outmod = target_pkg.module("app")
    if outmod.exists():
        logger.info("`{}` already exists. Skip generation.", outmod.path)
        return

    program = Program()
    program.import_("__future__.annotations", True)
    program.import_("litestar.Litestar", True)
    for route in routes:
        program.import_(route.path, False)

    program.root(
        stmt.LineBreak(),
        lambda ast: ast.assign(
            DeferredVar.simple("app_routes"),
            PredefinedFn.list(
                [expr.ExprIdent(route.path + ".router") for route in routes]
            ),
        ),
        lambda ast: ast.assign(
            DeferredVar.simple("app"),
            expr.ExprFuncCall(
                expr.ExprIdent("Litestar"),
                [
                    PredefinedFn.keyword_assignment(
                        "route_handlers",
                        expr.ExprIdent("app_routes"),
                    )
                ],
            ),
        ),
    )

    outmod.write(program)
