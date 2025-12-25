from __future__ import annotations

from typing import Sequence

from codegen.models import (
    AST,
    DeferredVar,
    ImportHelper,
    PredefinedFn,
    Program,
    expr,
    stmt,
)

from sera.make.py_backend.misc import get_python_property_name
from sera.misc import (
    assert_isinstance,
    assert_not_null,
    filter_duplication,
    to_snake_case,
)
from sera.models import (
    Cardinality,
    Class,
    DataProperty,
    IndexType,
    ObjectProperty,
    Package,
    Schema,
)
from sera.typing import GLOBAL_IDENTS, ObjectPath


def make_python_relational_model(
    schema: Schema,
    target_pkg: Package,
    target_data_pkg: Package,
    reference_classes: dict[str, ObjectPath],
):
    """Make python classes for relational database using SQLAlchemy.

    The new classes is going be compatible with SQLAlchemy 2.

    Args:
        schema: The schema to generate the classes from.
        target_pkg: The package to write the classes to.
        target_data_pkg: The package to write the data classes to.
        reference_classes: A dictionary of class names to their references (e.g., the ones that are defined outside and used as referenced such as Tenant).
    """
    app = target_pkg.app

    def make_base(custom_types: Sequence[ObjectProperty]):
        """Make a base class for our database."""
        program = Program()
        program.import_("__future__.annotations", True)
        program.import_("sera.libs.base_orm.BaseORM", True)
        program.import_("sera.libs.base_orm.create_engine", True)
        program.import_("sera.libs.base_orm.create_async_engine", True)
        program.import_("sqlalchemy.orm.DeclarativeBase", True)
        program.import_("sqlalchemy.orm.Session", True)
        program.import_("sqlalchemy.ext.asyncio.AsyncSession", True)
        program.import_("sqlalchemy.text", True)

        # assume configuration for the app at the top level
        program.import_(f"{app.config.path}.DB_CONNECTION", True)
        program.import_(f"{app.config.path}.DB_DEBUG", True)
        program.import_(f"contextlib.contextmanager", True)

        program.root.linebreak()

        type_map = []
        for custom_type in custom_types:
            program.import_(
                f"{target_data_pkg.module(custom_type.target.get_pymodule_name()).path}.{custom_type.target.name}",
                is_import_attr=True,
            )

            if custom_type.cardinality.is_star_to_many():
                if custom_type.is_map:
                    program.import_("sera.libs.base_orm.DictDataclassType", True)
                    type = f"dict[str, {custom_type.target.name}]"
                    maptype = f"DictDataclassType({custom_type.target.name})"
                else:
                    program.import_("sera.libs.base_orm.ListDataclassType", True)
                    type = f"list[{custom_type.target.name}]"
                    maptype = f"ListDataclassType({custom_type.target.name})"
            else:
                program.import_("sera.libs.base_orm.DataclassType", True)
                type = custom_type.target.name
                maptype = f"DataclassType({custom_type.target.name})"

            if custom_type.is_optional:
                program.import_("typing.Optional", True)
                type = f"Optional[{type}]"

            type_map.append((expr.ExprIdent(type), expr.ExprIdent(maptype)))

        program.root.class_(
            "Base", [expr.ExprIdent("DeclarativeBase"), expr.ExprIdent("BaseORM")]
        )(
            stmt.DefClassVarStatement(
                "type_annotation_map", "dict", PredefinedFn.dict(type_map)
            ),
            return_self=True,
        )

        program.root.linebreak()
        program.root.assign(
            DeferredVar.simple("engine"),
            expr.ExprFuncCall(
                expr.ExprIdent("create_engine"),
                [
                    expr.ExprIdent("DB_CONNECTION"),
                    PredefinedFn.keyword_assignment("echo", expr.ExprIdent("DB_DEBUG")),
                ],
            ),
        )
        program.root.assign(
            DeferredVar.simple("async_engine"),
            expr.ExprFuncCall(
                expr.ExprIdent("create_async_engine"),
                [
                    expr.ExprIdent("DB_CONNECTION"),
                    PredefinedFn.keyword_assignment("echo", expr.ExprIdent("DB_DEBUG")),
                ],
            ),
        )

        program.root.linebreak()
        program.root.func("create_db_and_tables", [])(
            stmt.PythonStatement("Base.metadata.create_all(engine)"),
        )

        program.root.linebreak()
        program.root.func("get_async_session", [], is_async=True)(
            lambda ast: ast.python_stmt(
                "async with AsyncSession(async_engine, expire_on_commit=False) as session:"
            )(
                lambda ast_l1: ast_l1.try_()(stmt.PythonStatement("yield session")),
                lambda ast_l1: ast_l1.catch()(
                    stmt.SingleExprStatement(
                        expr.ExprAwait(
                            expr.ExprFuncCall(
                                PredefinedFn.attr_getter(
                                    expr.ExprIdent("session"),
                                    expr.ExprIdent("rollback"),
                                ),
                                [],
                            )
                        )
                    ),
                    stmt.PythonStatement("raise"),
                ),
                lambda ast_l1: ast_l1.else_()(
                    stmt.SingleExprStatement(
                        expr.ExprAwait(
                            expr.ExprFuncCall(
                                PredefinedFn.attr_getter(
                                    expr.ExprIdent("session"), expr.ExprIdent("execute")
                                ),
                                [
                                    expr.ExprFuncCall(
                                        expr.ExprIdent("text"),
                                        [expr.ExprConstant("RESET ROLE;")],
                                    )
                                ],
                            )
                        )
                    ),
                    stmt.SingleExprStatement(
                        expr.ExprAwait(
                            expr.ExprFuncCall(
                                PredefinedFn.attr_getter(
                                    expr.ExprIdent("session"), expr.ExprIdent("commit")
                                ),
                                [],
                            )
                        )
                    ),
                ),
            )
        )

        program.root.linebreak()
        program.root.python_stmt("@contextmanager")
        program.root.func("get_session", [])(
            lambda ast: ast.python_stmt(
                "with Session(engine, expire_on_commit=False) as session:"
            )(
                lambda ast_l1: ast_l1.try_()(stmt.PythonStatement("yield session")),
                lambda ast_l1: ast_l1.catch()(
                    stmt.SingleExprStatement(
                        expr.ExprFuncCall(
                            PredefinedFn.attr_getter(
                                expr.ExprIdent("session"), expr.ExprIdent("rollback")
                            ),
                            [],
                        )
                    ),
                    stmt.PythonStatement("raise"),
                ),
                lambda ast_l1: ast_l1.else_()(
                    stmt.SingleExprStatement(
                        expr.ExprFuncCall(
                            PredefinedFn.attr_getter(
                                expr.ExprIdent("session"), expr.ExprIdent("execute")
                            ),
                            [
                                expr.ExprFuncCall(
                                    expr.ExprIdent("text"),
                                    [expr.ExprConstant("RESET ROLE;")],
                                )
                            ],
                        )
                    ),
                    stmt.SingleExprStatement(
                        expr.ExprFuncCall(
                            PredefinedFn.attr_getter(
                                expr.ExprIdent("session"), expr.ExprIdent("commit")
                            ),
                            [],
                        )
                    ),
                ),
            )
        )

        target_pkg.module("base").write(program)

    def make_db_schema_export():
        program = Program()
        program.import_("__future__.annotations", True)

        expose_vars = [
            expr.ExprConstant(cls.name)
            for cls in schema.classes.values()
            if cls.db is not None
        ]
        expose_vars.append(expr.ExprConstant("dbschema"))

        for name in ["engine", "async_engine", "get_session", "get_async_session"]:
            program.import_(f"{target_pkg.path}.base.{name}", True)
            expose_vars.append(expr.ExprConstant(name))

        output = []
        for cls in schema.classes.values():
            if cls.db is None:
                continue
            program.import_(
                f"{target_pkg.path}.{cls.get_pymodule_name()}.{cls.name}",
                True,
            )
            output.append((expr.ExprConstant(cls.name), expr.ExprIdent(cls.name)))

            # if there is a MANY-TO-MANY relationship, we need to add an association table as well
            for prop in cls.properties.values():
                if (
                    not isinstance(prop, ObjectProperty)
                    or prop.target.db is None
                    or prop.cardinality != Cardinality.MANY_TO_MANY
                ):
                    continue

                program.import_(
                    f"{target_pkg.path}.{to_snake_case(cls.name + prop.target.name)}.{cls.name}{prop.target.name}",
                    True,
                )
                output.append(
                    (
                        expr.ExprConstant(f"{cls.name}{prop.target.name}"),
                        expr.ExprIdent(f"{cls.name}{prop.target.name}"),
                    )
                )
                expose_vars.append(expr.ExprConstant(f"{cls.name}{prop.target.name}"))

        program.root(
            stmt.LineBreak(),
            lambda ast: ast.assign(
                DeferredVar.simple("dbschema"), PredefinedFn.dict(output)
            ),
            stmt.LineBreak(),
            lambda ast: ast.assign(
                DeferredVar.simple("__all__"),
                PredefinedFn.list(expose_vars),
            ),
        )

        target_pkg.module("__init__").write(program)

    def make_orm(cls: Class):
        if cls.db is None or cls.name in reference_classes:
            # skip classes that are not stored in the database
            return

        program = Program()
        program.import_("__future__.annotations", True)
        program.import_("sqlalchemy.orm.MappedAsDataclass", True)
        program.import_("sqlalchemy.orm.mapped_column", True)
        program.import_("sqlalchemy.orm.Mapped", True)
        program.import_(f"{target_pkg.path}.base.Base", True)

        ident_manager = ImportHelper(
            program,
            GLOBAL_IDENTS,
        )

        index_stmts = []

        if len(cls.db.indices) > 0 or any(
            isinstance(prop, DataProperty)
            and prop.db is not None
            and prop.db.is_indexed
            and (
                prop.db.index_type == IndexType.POSTGRES_FTS_SEVI
                or prop.db.index_type == IndexType.POSTGRES_TRIGRAM
            )
            for prop in cls.properties.values()
        ):
            program.import_("sqlalchemy.Index", True)

            fts_index = []
            for prop in cls.properties.values():
                if (
                    not isinstance(prop, DataProperty)
                    or prop.db is None
                    or not prop.db.is_indexed
                ):
                    continue
                propname = get_python_property_name(prop)
                if prop.db.index_type == IndexType.POSTGRES_FTS_SEVI:
                    fts_index.append(
                        expr.ExprFuncCall(
                            expr.ExprIdent("Index"),
                            [
                                expr.ExprConstant(
                                    f"ix_{cls.db.table_name}_{propname}_gin"
                                ),
                                expr.ExprFuncCall(
                                    ident_manager.use("text"),
                                    [
                                        expr.ExprConstant(
                                            f"to_tsvector('sevi', {propname})"
                                        )
                                    ],
                                ),
                                PredefinedFn.keyword_assignment(
                                    "postgresql_using", expr.ExprConstant("gin")
                                ),
                            ],
                        )
                    )
                if prop.db.index_type == IndexType.POSTGRES_TRIGRAM:
                    fts_index.append(
                        expr.ExprFuncCall(
                            expr.ExprIdent("Index"),
                            [
                                expr.ExprConstant(
                                    f"ix_{cls.db.table_name}_{propname}_gist"
                                ),
                                expr.ExprFuncCall(
                                    expr.ExprIdent("text"),
                                    [
                                        expr.ExprConstant(
                                            f"f_unaccent({propname}) gist_trgm_ops(siglen=256)"
                                        )
                                    ],
                                ),
                                PredefinedFn.keyword_assignment(
                                    "postgresql_using", expr.ExprConstant("gist")
                                ),
                            ],
                        )
                    )

            index_stmts.append(
                stmt.DefClassVarStatement(
                    "__table_args__",
                    None,
                    PredefinedFn.tuple(
                        fts_index
                        + [
                            expr.ExprFuncCall(
                                expr.ExprIdent("Index"),
                                [expr.ExprConstant(index.name)]
                                + [
                                    expr.ExprConstant(
                                        get_python_property_name(cls.properties[prop])
                                    )
                                    for prop in index.columns
                                ]
                                + (
                                    [
                                        PredefinedFn.keyword_assignment(
                                            "unique", expr.ExprConstant(index.unique)
                                        )
                                    ]
                                    if index.unique
                                    else []
                                ),
                            )
                            for index in cls.db.indices
                        ]
                    ),
                )
            )

        cls_ast = program.root.class_(
            cls.name, [expr.ExprIdent("MappedAsDataclass"), expr.ExprIdent("Base")]
        )
        cls_ast(
            stmt.DefClassVarStatement(
                "__tablename__",
                type=None,
                value=expr.ExprConstant(cls.db.table_name),
            ),
            *index_stmts,
            stmt.LineBreak(),
        )

        for prop in cls.properties.values():
            if prop.db is None:
                # skip properties that are not stored in the database
                continue

            if isinstance(prop, DataProperty):
                sqltype = prop.datatype.get_sqlalchemy_type()
                for dep in sqltype.deps:
                    program.import_(dep, True)

                propname = prop.name

                if prop.is_optional:
                    program.import_("typing.Optional", True)
                    proptype = f"Mapped[Optional[{sqltype.mapped_pytype}]]"
                else:
                    proptype = f"Mapped[{sqltype.mapped_pytype}]"

                propvalargs: list[expr.Expr] = [expr.ExprIdent(sqltype.type)]
                if prop.db.foreign_key is not None:
                    assert prop.db.foreign_key.db is not None, (
                        f"Foreign key {prop.db.foreign_key.name} must have a database mapping"
                    )
                    foreign_key_idprop = prop.db.foreign_key.get_id_property()
                    assert foreign_key_idprop is not None, (
                        f"Foreign key {prop.db.foreign_key.name} must have an id property"
                    )
                    propvalargs.append(
                        expr.ExprFuncCall(
                            ident_manager.use("ForeignKey"),
                            [
                                expr.ExprConstant(
                                    f"{prop.db.foreign_key.db.table_name}.{foreign_key_idprop.name}"
                                ),
                                PredefinedFn.keyword_assignment(
                                    "ondelete",
                                    expr.ExprConstant("CASCADE"),
                                ),
                                PredefinedFn.keyword_assignment(
                                    "onupdate",
                                    expr.ExprConstant("CASCADE"),
                                ),
                            ],
                        )
                    )
                if prop.db.is_primary_key:
                    propvalargs.append(
                        PredefinedFn.keyword_assignment(
                            "primary_key", expr.ExprConstant(True)
                        )
                    )
                    if prop.db.is_auto_increment:
                        propvalargs.append(
                            PredefinedFn.keyword_assignment(
                                "autoincrement", expr.ExprConstant("auto")
                            )
                        )
                else:
                    if prop.db.is_unique:
                        propvalargs.append(
                            PredefinedFn.keyword_assignment(
                                "unique", expr.ExprConstant(True)
                            )
                        )
                    elif prop.db.is_indexed and prop.db.index_type == IndexType.DEFAULT:
                        # only add index=True for default index type
                        propvalargs.append(
                            PredefinedFn.keyword_assignment(
                                "index", expr.ExprConstant(True)
                            )
                        )
                if prop.is_optional:
                    propvalargs.append(
                        PredefinedFn.keyword_assignment(
                            "nullable", expr.ExprConstant(True)
                        )
                    )
                propval = expr.ExprFuncCall(
                    expr.ExprIdent("mapped_column"), propvalargs
                )
                cls_ast(stmt.DefClassVarStatement(propname, proptype, propval))

                if prop.db.foreign_key is not None:
                    # add a relationship property for foreign key primary key so that we can do eager join in SQLAlchemy
                    program.import_("sqlalchemy.orm.relationship", True)
                    if prop.db.foreign_key.name != cls.name:
                        ident_manager.python_import_for_hint(
                            target_pkg.path
                            + f".{prop.db.foreign_key.get_pymodule_name()}.{prop.db.foreign_key.name}",
                            True,
                        )
                    cls_ast(
                        stmt.DefClassVarStatement(
                            propname + "_relobj",
                            f"Mapped[{prop.db.foreign_key.name}]",
                            expr.ExprFuncCall(
                                expr.ExprIdent("relationship"),
                                [
                                    PredefinedFn.keyword_assignment(
                                        "lazy",
                                        expr.ExprConstant("raise_on_sql"),
                                    ),
                                    PredefinedFn.keyword_assignment(
                                        "foreign_keys",
                                        expr.ExprIdent(propname),
                                    ),
                                    PredefinedFn.keyword_assignment(
                                        "init",
                                        expr.ExprConstant(False),
                                    ),
                                ],
                            ),
                        )
                    )
            else:
                assert isinstance(prop, ObjectProperty)
                make_python_relational_object_property(
                    program=program,
                    ident_manager=ident_manager,
                    target_pkg=target_pkg,
                    target_data_pkg=target_data_pkg,
                    cls_ast=cls_ast,
                    cls=cls,
                    prop=prop,
                    custom_types=custom_types,
                )

        target_pkg.module(cls.get_pymodule_name()).write(program)

    custom_types: list[ObjectProperty] = []

    for cls in schema.topological_sort():
        make_orm(cls)

    # make a base class that implements the mapping for custom types
    custom_types = filter_duplication(
        custom_types, lambda p: (p.target.name, p.cardinality, p.is_optional, p.is_map)
    )
    make_base(custom_types)

    # export the db classes in the __init__ file
    make_db_schema_export()


def make_python_relational_object_property(
    program: Program,
    ident_manager: ImportHelper,
    target_pkg: Package,
    target_data_pkg: Package,
    cls_ast: AST,
    cls: Class,
    prop: ObjectProperty,
    custom_types: list[ObjectProperty],
):
    assert prop.db is not None
    if prop.target.db is not None:
        # if the target class is in the database, we generate a foreign key for it.
        program.import_("sqlalchemy.ForeignKey", True)

        if prop.cardinality == Cardinality.MANY_TO_MANY:
            make_python_relational_object_property_many_to_many(
                program, cls_ast, target_pkg, cls, prop
            )
            return

        if prop.cardinality.is_star_to_many():
            raise NotImplementedError((cls.name, prop.name))

        program.import_("sqlalchemy.orm.relationship", True)
        if prop.target.name != cls.name:
            ident_manager.python_import_for_hint(
                target_pkg.path
                + f".{prop.target.get_pymodule_name()}.{prop.target.name}",
                True,
            )

        # we store this class in the database
        propname = get_python_property_name(prop)
        idprop = prop.target.get_id_property()
        assert idprop is not None
        idprop_pytype = idprop.datatype.get_sqlalchemy_type()

        if prop.is_optional:
            idprop_pytype = idprop_pytype.as_optional_type()

        for dep in idprop_pytype.deps:
            program.import_(dep, True)

        proptype = f"Mapped[{idprop_pytype.mapped_pytype}]"
        propval = expr.ExprFuncCall(
            expr.ExprIdent("mapped_column"),
            [
                expr.ExprIdent(idprop_pytype.type),
                expr.ExprFuncCall(
                    expr.ExprIdent("ForeignKey"),
                    [
                        expr.ExprConstant(f"{prop.target.db.table_name}.{idprop.name}"),
                        PredefinedFn.keyword_assignment(
                            "ondelete",
                            expr.ExprConstant(prop.db.on_target_delete.to_sqlalchemy()),
                        ),
                        PredefinedFn.keyword_assignment(
                            "onupdate",
                            expr.ExprConstant(prop.db.on_target_update.to_sqlalchemy()),
                        ),
                    ],
                ),
                PredefinedFn.keyword_assignment(
                    "nullable",
                    expr.ExprConstant(prop.is_optional),
                ),
            ],
        )

        cls_ast(
            stmt.DefClassVarStatement(propname, proptype, propval),
            stmt.DefClassVarStatement(
                prop.name,
                f"Mapped[{prop.target.name}]",
                expr.ExprFuncCall(
                    expr.ExprIdent("relationship"),
                    [
                        PredefinedFn.keyword_assignment(
                            "lazy",
                            expr.ExprConstant("raise_on_sql"),
                        ),
                        PredefinedFn.keyword_assignment(
                            "foreign_keys",
                            expr.ExprIdent(propname),
                        ),
                        PredefinedFn.keyword_assignment(
                            "init",
                            expr.ExprConstant(False),
                        ),
                    ],
                ),
            ),
        )
        return

    # if the target class is not in the database,
    program.import_(
        f"{target_data_pkg.module(prop.target.get_pymodule_name()).path}.{prop.target.name}",
        is_import_attr=True,
    )
    propname = prop.name
    if prop.cardinality.is_star_to_many():
        if prop.is_map:
            proptype = f"Mapped[dict[str, {prop.target.name}]]"
        else:
            proptype = f"Mapped[list[{prop.target.name}]]"
    else:
        if prop.is_optional:
            program.import_("typing.Optional", True)
            proptype = f"Mapped[Optional[{prop.target.name}]]"
        else:
            proptype = f"Mapped[{prop.target.name}]"

    # we have two choices, one is to create a composite class, one is to create a custom field
    if prop.db.is_embedded == "composite":
        assert not prop.cardinality.is_star_to_many()
        # for a class to be composite, it must have only data properties
        program.import_("sqlalchemy.orm.composite", True)
        if prop.is_optional:
            propvalargs: list[expr.Expr] = [
                expr.ExprIdent(prop.target.name + ".init_optional")
            ]
        else:
            propvalargs: list[expr.Expr] = [expr.ExprIdent(prop.target.name)]

        for p in prop.target.properties.values():
            pdtype = assert_isinstance(p, DataProperty).datatype.get_sqlalchemy_type()
            for dep in pdtype.deps:
                program.import_(dep, True)

            propvalargs.append(
                expr.ExprFuncCall(
                    expr.ExprIdent("mapped_column"),
                    [
                        expr.ExprConstant(f"{prop.name}_{p.name}"),
                        expr.ExprIdent(pdtype.type),
                        PredefinedFn.keyword_assignment(
                            "nullable",
                            expr.ExprConstant(prop.is_optional or p.is_optional),
                        ),
                    ],
                )
            )
        propval = expr.ExprFuncCall(
            expr.ExprIdent("composite"),
            propvalargs,
        )
    else:
        assert prop.db.is_embedded == "json"
        # we create a custom field, the custom field mapping need to be defined in the base
        propval = expr.ExprFuncCall(
            expr.ExprIdent("mapped_column"),
            [
                PredefinedFn.keyword_assignment(
                    "nullable",
                    expr.ExprConstant(prop.is_optional),
                ),
            ],
        )
        custom_types.append(prop)

    cls_ast(stmt.DefClassVarStatement(propname, proptype, propval))


def make_python_relational_object_property_many_to_many(
    program: Program,
    ast: AST,
    target_pkg: Package,
    cls: Class,
    prop: ObjectProperty,
):
    assert cls.db is not None
    assert prop.db is not None and prop.target.db is not None
    assert prop.cardinality == Cardinality.MANY_TO_MANY

    # we create a new table to store the many-to-many relationship
    new_table = f"{cls.name}{prop.target.name}"
    clsdb = cls.db
    propdb = prop.db
    targetdb = prop.target.db

    source_idprop = assert_not_null(cls.get_id_property())
    source_id_type = source_idprop.datatype.get_python_type().type
    target_idprop = assert_not_null(prop.target.get_id_property())
    target_id_type = target_idprop.datatype.get_python_type().type

    newprogram = Program()
    newprogram.import_("__future__.annotations", True)
    newprogram.import_("sqlalchemy.ForeignKey", True)
    newprogram.import_("sqlalchemy.orm.mapped_column", True)
    newprogram.import_("sqlalchemy.orm.Mapped", True)
    newprogram.import_("sqlalchemy.orm.relationship", True)
    newprogram.import_(f"{target_pkg.path}.base.Base", True)

    ident_manager = ImportHelper(
        newprogram,
        GLOBAL_IDENTS,
    )

    ident_manager.python_import_for_hint(
        target_pkg.path + f".{cls.get_pymodule_name()}.{cls.name}",
        is_import_attr=True,
    )
    ident_manager.python_import_for_hint(
        target_pkg.path + f".{prop.target.get_pymodule_name()}.{prop.target.name}",
        is_import_attr=True,
    )

    newprogram.root(
        stmt.LineBreak(),
        lambda ast00: ast00.class_(new_table, [expr.ExprIdent("Base")])(
            stmt.DefClassVarStatement(
                "__tablename__",
                type=None,
                value=expr.ExprConstant(f"{clsdb.table_name}_{targetdb.table_name}"),
            ),
            stmt.LineBreak(),
            stmt.DefClassVarStatement(
                to_snake_case(cls.name),
                f"Mapped[{cls.name}]",
                expr.ExprFuncCall(
                    expr.ExprIdent("relationship"),
                    [
                        PredefinedFn.keyword_assignment(
                            "back_populates",
                            expr.ExprConstant(prop.name),
                        ),
                        PredefinedFn.keyword_assignment(
                            "lazy",
                            expr.ExprConstant("raise_on_sql"),
                        ),
                    ],
                ),
            ),
            stmt.DefClassVarStatement(
                to_snake_case(cls.name) + "_id",
                f"Mapped[{source_id_type}]",
                expr.ExprFuncCall(
                    expr.ExprIdent("mapped_column"),
                    [
                        expr.ExprFuncCall(
                            expr.ExprIdent("ForeignKey"),
                            [
                                expr.ExprConstant(
                                    f"{clsdb.table_name}.{source_idprop.name}"
                                ),
                                PredefinedFn.keyword_assignment(
                                    "ondelete",
                                    expr.ExprConstant(
                                        propdb.on_source_delete.to_sqlalchemy()
                                    ),
                                ),
                                PredefinedFn.keyword_assignment(
                                    "onupdate",
                                    expr.ExprConstant(
                                        propdb.on_source_update.to_sqlalchemy()
                                    ),
                                ),
                            ],
                        ),
                        PredefinedFn.keyword_assignment(
                            "primary_key", expr.ExprConstant(True)
                        ),
                    ],
                ),
            ),
            stmt.DefClassVarStatement(
                to_snake_case(prop.target.name),
                f"Mapped[{prop.target.name}]",
                expr.ExprFuncCall(
                    expr.ExprIdent("relationship"),
                    [
                        PredefinedFn.keyword_assignment(
                            "lazy",
                            expr.ExprConstant("raise_on_sql"),
                        ),
                    ],
                ),
            ),
            stmt.DefClassVarStatement(
                to_snake_case(prop.target.name) + "_id",
                f"Mapped[{target_id_type}]",
                expr.ExprFuncCall(
                    expr.ExprIdent("mapped_column"),
                    [
                        expr.ExprFuncCall(
                            expr.ExprIdent("ForeignKey"),
                            [
                                expr.ExprConstant(
                                    f"{targetdb.table_name}.{target_idprop.name}"
                                ),
                                PredefinedFn.keyword_assignment(
                                    "ondelete",
                                    expr.ExprConstant(
                                        propdb.on_target_delete.to_sqlalchemy()
                                    ),
                                ),
                                PredefinedFn.keyword_assignment(
                                    "onupdate",
                                    expr.ExprConstant(
                                        propdb.on_target_update.to_sqlalchemy()
                                    ),
                                ),
                            ],
                        ),
                        PredefinedFn.keyword_assignment(
                            "primary_key", expr.ExprConstant(True)
                        ),
                    ],
                ),
            ),
        ),
    )

    new_table_module = target_pkg.module(to_snake_case(new_table))
    new_table_module.write(newprogram)

    # now we add the relationship to the source.
    # we can configure it to be list, set, or dict depends on what we want.
    program.import_(new_table_module.path + f".{new_table}", True)
    program.import_("sqlalchemy.orm.relationship", True)

    # program.import_("typing.TYPE_CHECKING", True)
    # program.import_area.if_(expr.ExprIdent("TYPE_CHECKING"))(
    #     lambda ast00: ast00.import_(
    #         target_pkg.path + f".{prop.target.get_pymodule_name()}.{prop.target.name}",
    #         is_import_attr=True,
    #     )
    # )

    ast(
        stmt.DefClassVarStatement(
            prop.name,
            f"Mapped[list[{new_table}]]",
            expr.ExprFuncCall(
                expr.ExprIdent("relationship"),
                [
                    PredefinedFn.keyword_assignment(
                        "back_populates",
                        expr.ExprConstant(to_snake_case(cls.name)),
                    ),
                    PredefinedFn.keyword_assignment(
                        "lazy",
                        expr.ExprConstant("raise_on_sql"),
                    ),
                ],
            ),
        ),
    )
