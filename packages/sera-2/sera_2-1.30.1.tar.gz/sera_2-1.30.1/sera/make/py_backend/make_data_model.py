from __future__ import annotations

from typing import Callable, Literal, Optional

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
    assert_not_null,
    to_snake_case,
)
from sera.models import (
    Cardinality,
    Class,
    DataProperty,
    ObjectProperty,
    Package,
    PyTypeWithDep,
    Schema,
)
from sera.typing import GLOBAL_IDENTS, ObjectPath


def make_python_data_model(
    schema: Schema, target_pkg: Package, reference_classes: dict[str, ObjectPath]
):
    """Generate public classes for the API from the schema.

    Args:
        schema: The schema to generate the classes from.
        target_pkg: The package to write the classes to.
        reference_classes: A dictionary of class names to their references (e.g., the ones that are defined outside and used as referenced such as Tenant).
    """
    app = target_pkg.app

    def from_db_type_conversion(
        record: expr.ExprIdent,
        prop: DataProperty | ObjectProperty,
        value_pass_as_args: Optional[expr.Expr] = None,
    ):
        """Convert the value from the database to the data model type.

        Args:
            record: The record to convert from.
            prop: The property to convert.
            value_pass_as_args: If provided, this value will be used instead of getting the value from the record. This is useful for functions that
                receive the column value as an argument, such as the `as_composite` function.
        """
        if value_pass_as_args is not None:
            value = value_pass_as_args
            assert record == expr.ExprIdent(""), (
                "If value_pass_as_args is provided, record should not be used as a dummy value should be passed instead."
            )
        else:
            value = PredefinedFn.attr_getter(record, expr.ExprIdent(prop.name))

        propname = get_python_property_name(prop)
        if isinstance(prop, ObjectProperty) and prop.target.db is not None:
            if prop.cardinality.is_star_to_many():
                value = PredefinedFn.map_list(
                    value,
                    lambda item: PredefinedFn.attr_getter(
                        item, expr.ExprIdent(propname)
                    ),
                )
            else:
                assert value_pass_as_args is None, (
                    "Cannot use value_pass_as_args for a single object property."
                )
                value = PredefinedFn.attr_getter(record, expr.ExprIdent(propname))

            target_idprop = assert_not_null(prop.target.get_id_property())
            conversion_fn = get_data_conversion(
                target_idprop.datatype.get_python_type().type,
                target_idprop.get_data_model_datatype().get_python_type().type,
            )
            value = conversion_fn(value)
        elif isinstance(prop, DataProperty) and prop.is_diff_data_model_datatype():
            value = get_data_conversion(
                prop.datatype.get_python_type().type,
                prop.get_data_model_datatype().get_python_type().type,
            )(value)

        return value

    def to_db_type_conversion(
        program: Program,
        slf: expr.ExprIdent,
        cls: Class,
        mode: Literal["create", "update"],
        prop: DataProperty | ObjectProperty,
    ):
        propname = get_python_property_name(prop)

        value = PredefinedFn.attr_getter(slf, expr.ExprIdent(propname))
        if isinstance(prop, ObjectProperty):
            if (
                prop.target.db is not None
                and prop.cardinality == Cardinality.MANY_TO_MANY
            ):
                # we have to use the associated object
                # if this isn't a many-to-many relationship, we only keep the id, so no need to convert to the type.
                AssociationTable = f"{cls.name}{prop.target.name}"
                program.import_(
                    app.models.db.path
                    + f".{to_snake_case(AssociationTable)}.{AssociationTable}",
                    True,
                )

                target_idprop = assert_not_null(prop.target.get_id_property())
                conversion_fn = get_data_conversion(
                    target_idprop.get_data_model_datatype().get_python_type().type,
                    target_idprop.datatype.get_python_type().type,
                )

                return PredefinedFn.map_list(
                    value,
                    lambda item: expr.ExprFuncCall(
                        expr.ExprIdent(AssociationTable),
                        [
                            PredefinedFn.keyword_assignment(
                                propname, conversion_fn(item)
                            )
                        ],
                    ),
                )
            elif prop.target.db is None:
                # if the target class is not in the database, we need to convert the value to the python type used in db.
                # if the cardinality is many-to-many, we need to convert each item in the list.
                if prop.cardinality.is_star_to_many():
                    value = PredefinedFn.map_list(
                        value, lambda item: expr.ExprMethodCall(item, "to_db", [])
                    )
                elif prop.is_optional:
                    # we need to handle optional case for a single object, *-to-many uses
                    # a list and won't contain null
                    value = expr.ExprTernary(
                        expr.ExprNegation(expr.ExprIs(value, expr.ExprConstant(None))),
                        expr.ExprMethodCall(value, "to_db", []),
                        expr.ExprConstant(None),
                    )
                else:
                    value = expr.ExprMethodCall(value, "to_db", [])
        elif isinstance(prop, DataProperty) and prop.is_diff_data_model_datatype():
            # convert the value to the python type used in db
            converted_value = get_data_conversion(
                prop.get_data_model_datatype().get_python_type().type,
                prop.datatype.get_python_type().type,
            )(value)

            if mode == "update" and prop.data.is_private:
                # if the property is private and it's UNSET, we cannot transform it to the database type
                # and has to use the UNSET value (the update query will ignore this field)
                program.import_("sera.typing.UNSET", True)
                program.import_("sera.typing.is_set", True)
                value = expr.ExprTernary(
                    expr.ExprFuncCall(expr.ExprIdent("is_set"), [value]),
                    converted_value,
                    expr.ExprIdent("UNSET"),
                )
            else:
                value = converted_value
        return value

    def make_uscp_func(
        cls: Class,
        mode: Literal["create", "update"],
        ast: AST,
        ident_manager: ImportHelper,
    ):
        func = ast.func(
            "update_system_controlled_props",
            [
                DeferredVar.simple("self"),
                DeferredVar.simple(
                    "conn",
                    ident_manager.use("ASGIConnection"),
                ),
            ],
        )

        assign_user = False

        for prop in cls.properties.values():
            if prop.data.system_controlled is None:
                continue

            propname = get_python_property_name(prop)

            update_func = None
            if mode == "create":
                if prop.data.system_controlled.on_create_bypass is not None:
                    # by-pass the update function are handled later
                    continue

                if prop.data.system_controlled.is_on_create_value_updated():
                    update_func = (
                        prop.data.system_controlled.get_on_create_update_func()
                    )
            else:
                if prop.data.system_controlled.on_update_bypass is not None:
                    # by-pass the update function are handled later
                    continue
                if prop.data.system_controlled.is_on_update_value_updated():
                    update_func = (
                        prop.data.system_controlled.get_on_update_update_func()
                    )

            if update_func is None:
                continue

            if update_func.func == "getattr":
                if update_func.args[0] == "user":
                    if len(update_func.args) != 2:
                        raise NotImplementedError(
                            f"Unsupported update function: {update_func.func} with args {update_func.args}"
                        )
                    if not assign_user:
                        func(
                            stmt.AssignStatement(
                                expr.ExprIdent("user"),
                                PredefinedFn.item_getter(
                                    PredefinedFn.attr_getter(
                                        expr.ExprIdent("conn"),
                                        expr.ExprIdent("scope"),
                                    ),
                                    expr.ExprConstant("user"),
                                ),
                            )
                        )
                        assign_user = True
                    epr = PredefinedFn.attr_getter(
                        expr.ExprIdent("user"), expr.ExprIdent(update_func.args[1])
                    )
                elif update_func.args[0] == "self":
                    epr = PredefinedFn.attr_getter(
                        expr.ExprIdent("self"), expr.ExprIdent(update_func.args[1])
                    )
                else:
                    raise NotImplementedError(
                        f"Unsupported update function: {update_func.func} with args {update_func.args}"
                    )
            else:
                raise NotImplementedError(update_func.func)

            smt = stmt.AssignStatement(
                PredefinedFn.attr_getter(
                    expr.ExprIdent("self"), expr.ExprIdent(propname)
                ),
                epr,
            )
            func(smt)

        # handle the by-pass properties here
        for prop in cls.properties.values():
            if prop.data.system_controlled is None:
                continue

            update_func = None
            if mode == "create":
                if prop.data.system_controlled.on_create_bypass is None:
                    # non by-pass the update function are handled earlier
                    continue

                if prop.data.system_controlled.is_on_create_value_updated():
                    update_func = (
                        prop.data.system_controlled.get_on_create_update_func()
                    )
            else:
                if prop.data.system_controlled.on_update_bypass is None:
                    # non by-pass the update function are handled earlier
                    continue

                if prop.data.system_controlled.is_on_update_value_updated():
                    update_func = (
                        prop.data.system_controlled.get_on_update_update_func()
                    )

            if update_func is None:
                continue

            raise NotImplementedError("We haven't handled the by-pass properties yet.")

        func(
            stmt.AssignStatement(
                PredefinedFn.attr_getter(
                    expr.ExprIdent("self"), expr.ExprIdent("_is_scp_updated")
                ),
                expr.ExprConstant(True),
            )
        )

    def make_create(program: Program, cls: Class):
        program.import_("__future__.annotations", True)
        program.import_("msgspec", False)
        if cls.db is not None:
            # if the class is stored in the database, we need to import the database module
            program.import_(
                app.models.db.path + f".{cls.get_pymodule_name()}.{cls.name}",
                True,
                alias=f"{cls.name}DB",
            )

        ident_manager = ImportHelper(
            program,
            GLOBAL_IDENTS,
        )

        is_on_create_value_updated = any(
            prop.data.system_controlled is not None
            and prop.data.system_controlled.is_on_create_value_updated()
            for prop in cls.properties.values()
        )
        program.root.linebreak()
        cls_ast = program.root.class_(
            "Create" + cls.name,
            [expr.ExprIdent("msgspec.Struct"), expr.ExprIdent("kw_only=True")],
        )
        for prop in cls.properties.values():
            # Skip fields that are system-controlled (e.g., cached or derived fields)
            # and cannot be updated based on information parsed from the request.
            if (
                prop.data.system_controlled is not None
                and prop.data.system_controlled.is_on_create_ignored()
            ):
                continue

            propname = get_python_property_name(prop)
            if isinstance(prop, DataProperty):
                pytype = prop.get_data_model_datatype().get_python_type().clone()
                if len(prop.data.constraints) > 0:
                    # if the property has constraints, we need to figure out
                    program.import_("typing.Annotated", True)
                    if len(prop.data.constraints) == 1:
                        pytype.type = "Annotated[%s, %s]" % (
                            pytype.type,
                            prop.data.constraints[0].get_msgspec_constraint(),
                        )
                    else:
                        raise NotImplementedError(prop.data.constraints)

                if prop.is_optional:
                    pytype = pytype.as_optional_type()

                for dep in pytype.deps:
                    program.import_(dep, True)

                # private property are available for creating, but not for updating.
                # so we do not need to skip it.
                # if prop.data.is_private:
                #     program.import_("typing.Union", True)
                #     program.import_("sera.typing.UnsetType", True)
                #     program.import_("sera.typing.UNSET", True)
                #     pytype_type = f"Union[{pytype_type}, UnsetType]"

                prop_default_value = None
                # if prop.data.is_private:
                #     prop_default_value = expr.ExprIdent("UNSET")
                if prop.default_value is not None:
                    prop_default_value = expr.ExprConstant(prop.default_value)
                elif prop.default_factory is not None:
                    program.import_(prop.default_factory.pyfunc, True)
                    prop_default_value = expr.ExprFuncCall(
                        expr.ExprIdent("msgspec.field"),
                        [
                            PredefinedFn.keyword_assignment(
                                "default_factory",
                                expr.ExprIdent(prop.default_factory.pyfunc),
                            )
                        ],
                    )

                cls_ast(
                    stmt.DefClassVarStatement(propname, pytype.type, prop_default_value)
                )
            elif isinstance(prop, ObjectProperty):
                if prop.target.db is not None:
                    # if the target class is in the database, we expect the user to pass the foreign key for it.
                    pytype = (
                        assert_not_null(prop.target.get_id_property())
                        .get_data_model_datatype()
                        .get_python_type()
                    )
                else:
                    pytype = PyTypeWithDep(
                        f"Create{prop.target.name}",
                        [
                            f"{target_pkg.module(prop.target.get_pymodule_name()).path}.Create{prop.target.name}"
                        ],
                    )

                if prop.cardinality.is_star_to_many():
                    pytype = pytype.as_list_type()
                elif prop.is_optional:
                    pytype = pytype.as_optional_type()

                for dep in pytype.deps:
                    program.import_(dep, True)

                cls_ast(stmt.DefClassVarStatement(propname, pytype.type))

        if is_on_create_value_updated:
            program.import_("typing.Optional", True)
            program.import_("sera.typing.is_set", True)
            cls_ast(
                stmt.Comment(
                    "A marker to indicate that the system-controlled properties are updated"
                ),
                stmt.DefClassVarStatement(
                    "_is_scp_updated", "bool", expr.ExprConstant(False)
                ),
                stmt.LineBreak(),
                lambda ast: ast.func(
                    "__post_init__",
                    [
                        DeferredVar.simple("self"),
                    ],
                )(
                    stmt.AssignStatement(
                        PredefinedFn.attr_getter(
                            expr.ExprIdent("self"), expr.ExprIdent("_is_scp_updated")
                        ),
                        expr.ExprConstant(False),
                    ),
                ),
                stmt.LineBreak(),
                lambda ast: make_uscp_func(cls, "create", ast, ident_manager),
            )

        cls_ast(
            stmt.LineBreak(),
            lambda ast00: ast00.func(
                "to_db",
                [
                    DeferredVar.simple("self"),
                ],
                return_type=expr.ExprIdent(
                    f"{cls.name}DB" if cls.db is not None else cls.name
                ),
            )(
                (
                    stmt.AssertionStatement(
                        PredefinedFn.attr_getter(
                            expr.ExprIdent("self"),
                            expr.ExprIdent("_is_scp_updated"),
                        ),
                        expr.ExprConstant(
                            "The model data must be verified before converting to db model"
                        ),
                    )
                    if is_on_create_value_updated
                    else None
                ),
                lambda ast10: ast10.return_(
                    expr.ExprFuncCall(
                        expr.ExprIdent(
                            f"{cls.name}DB" if cls.db is not None else cls.name
                        ),
                        [
                            (
                                ident_manager.use("UNSET")
                                if prop.data.system_controlled is not None
                                and prop.data.system_controlled.is_on_create_ignored()
                                else to_db_type_conversion(
                                    program, expr.ExprIdent("self"), cls, "create", prop
                                )
                            )
                            for prop in cls.properties.values()
                        ],
                    )
                ),
            ),
        )

    def make_update(program: Program, cls: Class):
        program.import_("__future__.annotations", True)
        program.import_("msgspec", False)
        if cls.db is not None:
            # if the class is stored in the database, we need to import the database module
            program.import_(
                app.models.db.path + f".{cls.get_pymodule_name()}.{cls.name}",
                True,
                alias=f"{cls.name}DB",
            )

        ident_manager = ImportHelper(
            program,
            GLOBAL_IDENTS,
        )

        # property that normal users cannot set, but super users can
        is_on_update_value_updated = any(
            prop.data.system_controlled is not None
            and prop.data.system_controlled.is_on_update_value_updated()
            for prop in cls.properties.values()
        )

        program.root.linebreak()
        cls_ast = program.root.class_(
            "Update" + cls.name,
            [expr.ExprIdent("msgspec.Struct"), expr.ExprIdent("kw_only=True")],
        )
        for prop in cls.properties.values():
            # Skip fields that are system-controlled (e.g., cached or derived fields)
            # and cannot be updated based on information parsed from the request.
            if (
                prop.data.system_controlled is not None
                and prop.data.system_controlled.is_on_update_ignored()
            ):
                continue

            propname = get_python_property_name(prop)

            if isinstance(prop, DataProperty):
                pytype = prop.get_data_model_datatype().get_python_type().clone()

                if len(prop.data.constraints) > 0:
                    # if the property has constraints, we need to figure out
                    program.import_("typing.Annotated", True)
                    if len(prop.data.constraints) == 1:
                        pytype.type = "Annotated[%s, %s]" % (
                            pytype.type,
                            prop.data.constraints[0].get_msgspec_constraint(),
                        )
                    else:
                        raise NotImplementedError(prop.data.constraints)

                if prop.is_optional:
                    pytype = pytype.as_optional_type()

                for dep in pytype.deps:
                    program.import_(dep, True)

                if prop.data.is_private:
                    program.import_("typing.Union", True)
                    program.import_("sera.typing.UnsetType", True)
                    program.import_("sera.typing.UNSET", True)
                    pytype.type = f"Union[{pytype.type}, UnsetType]"

                prop_default_value = None
                if prop.data.is_private:
                    prop_default_value = expr.ExprIdent("UNSET")
                elif prop.default_value is not None:
                    prop_default_value = expr.ExprConstant(prop.default_value)
                elif prop.default_factory is not None:
                    program.import_(prop.default_factory.pyfunc, True)
                    prop_default_value = expr.ExprFuncCall(
                        expr.ExprIdent("msgspec.field"),
                        [
                            PredefinedFn.keyword_assignment(
                                "default_factory",
                                expr.ExprIdent(prop.default_factory.pyfunc),
                            )
                        ],
                    )

                cls_ast(
                    stmt.DefClassVarStatement(propname, pytype.type, prop_default_value)
                )
            elif isinstance(prop, ObjectProperty):
                if prop.target.db is not None:
                    # if the target class is in the database, we expect the user to pass the foreign key for it.
                    pytype = (
                        assert_not_null(prop.target.get_id_property())
                        .get_data_model_datatype()
                        .get_python_type()
                    )

                else:
                    pytype = PyTypeWithDep(
                        f"Update{prop.target.name}",
                        [
                            f"{target_pkg.module(prop.target.get_pymodule_name()).path}.Update{prop.target.name}"
                        ],
                    )

                if prop.cardinality.is_star_to_many():
                    pytype = pytype.as_list_type()
                elif prop.is_optional:
                    pytype = pytype.as_optional_type()

                for dep in pytype.deps:
                    program.import_(dep, True)

                cls_ast(stmt.DefClassVarStatement(propname, pytype.type))

        if is_on_update_value_updated:
            program.import_("typing.Optional", True)
            program.import_("sera.typing.is_set", True)
            cls_ast(
                stmt.Comment(
                    "A marker to indicate that the system-controlled properties are updated"
                ),
                stmt.DefClassVarStatement(
                    "_is_scp_updated", "bool", expr.ExprConstant(False)
                ),
                stmt.LineBreak(),
                lambda ast: ast.func(
                    "__post_init__",
                    [
                        DeferredVar.simple("self"),
                    ],
                )(
                    stmt.AssignStatement(
                        PredefinedFn.attr_getter(
                            expr.ExprIdent("self"), expr.ExprIdent("_is_scp_updated")
                        ),
                        expr.ExprConstant(False),
                    ),
                ),
                stmt.LineBreak(),
                lambda ast: make_uscp_func(cls, "update", ast, ident_manager),
            )

        cls_ast(
            stmt.LineBreak(),
            lambda ast00: ast00.func(
                "to_db",
                [
                    DeferredVar.simple("self"),
                ],
                return_type=expr.ExprIdent(
                    f"{cls.name}DB" if cls.db is not None else cls.name
                ),
            )(
                (
                    stmt.AssertionStatement(
                        expr.ExprLogicalAnd(
                            [
                                expr.ExprFuncCall(
                                    expr.ExprIdent("is_set"),
                                    [
                                        PredefinedFn.attr_getter(
                                            expr.ExprIdent("self"),
                                            expr.ExprIdent(
                                                get_python_property_name(prop)
                                            ),
                                        )
                                    ],
                                )
                                for prop in cls.properties.values()
                                if prop.data.system_controlled is not None
                                and prop.data.system_controlled.is_on_update_value_updated()
                            ]
                        ),
                        expr.ExprConstant(
                            "The model data must be verified before converting to db model"
                        ),
                    )
                    if is_on_update_value_updated
                    else None
                ),
                lambda ast10: ast10.return_(
                    expr.ExprFuncCall(
                        expr.ExprIdent(
                            f"{cls.name}DB" if cls.db is not None else cls.name
                        ),
                        [
                            (
                                ident_manager.use("UNSET")
                                if prop.data.system_controlled is not None
                                and prop.data.system_controlled.is_on_update_ignored()
                                else to_db_type_conversion(
                                    program, expr.ExprIdent("self"), cls, "update", prop
                                )
                            )
                            for prop in cls.properties.values()
                        ],
                    )
                ),
            ),
        )

    def make_normal(program: Program, cls: Class):
        if not cls.is_public:
            # skip classes that are not public
            return

        program.import_("__future__.annotations", True)
        program.import_("msgspec", False)

        ident_manager = ImportHelper(
            program,
            GLOBAL_IDENTS,
        )

        if cls.db is not None:
            # if the class is stored in the database, we need to import the database module
            program.import_(
                app.models.db.path + f".{cls.get_pymodule_name()}.{cls.name}",
                True,
                alias=f"{cls.name}DB",
            )

        cls_ast = program.root.class_(cls.name, [expr.ExprIdent("msgspec.Struct")])
        for prop in cls.properties.values():
            if prop.data.is_private:
                # skip private fields as this is for APIs exchange
                continue

            propname = get_python_property_name(prop)
            if isinstance(prop, DataProperty):
                pytype = prop.get_data_model_datatype().get_python_type()
                if prop.is_optional:
                    pytype = pytype.as_optional_type()

                for dep in pytype.deps:
                    program.import_(dep, True)

                cls_ast(stmt.DefClassVarStatement(propname, pytype.type))
            elif isinstance(prop, ObjectProperty):
                if prop.target.db is not None:
                    pytype = (
                        assert_not_null(prop.target.get_id_property())
                        .get_data_model_datatype()
                        .get_python_type()
                    )
                else:
                    pytype = PyTypeWithDep(
                        prop.target.name,
                        [
                            f"{target_pkg.module(prop.target.get_pymodule_name()).path}.{prop.target.name}"
                        ],
                    )

                if prop.cardinality.is_star_to_many():
                    pytype = pytype.as_list_type()
                elif prop.is_optional:
                    pytype = pytype.as_optional_type()

                for dep in pytype.deps:
                    program.import_(dep, True)

                cls_ast(stmt.DefClassVarStatement(propname, pytype.type))

        cls_ast(
            stmt.LineBreak(),
            (
                stmt.PythonDecoratorStatement(
                    expr.ExprFuncCall(expr.ExprIdent("classmethod"), [])
                )
                if cls.db is not None
                else None
            ),
            lambda ast00: (
                ast00.func(
                    "from_db",
                    [
                        DeferredVar.simple("cls"),
                        DeferredVar.simple("record", expr.ExprIdent(f"{cls.name}DB")),
                    ],
                )(
                    lambda ast10: ast10.return_(
                        expr.ExprFuncCall(
                            expr.ExprIdent("cls"),
                            [
                                from_db_type_conversion(expr.ExprIdent("record"), prop)
                                for prop in cls.properties.values()
                                if not prop.data.is_private
                            ],
                        )
                    )
                )
                if cls.db is not None
                else None
            ),
        )

        # generate composite functions for classes that can be used as embedded functions
        if cls.db is None:
            init_optional_args = [DeferredVar.simple("cls")]
            init_optional_null_condition = []
            for prop in cls.properties.values():
                propname = get_python_property_name(prop)

                assert not prop.data.is_private, (
                    f"Embedded classes should not have private properties: {cls.name}.{propname}"
                )
                init_optional_args.append(DeferredVar.simple(propname))
                init_optional_null_condition.append(
                    expr.ExprIs(expr.ExprIdent(propname), expr.ExprConstant(None))
                )

            # For simplicity, we assume that this embedded class can be used in a nullable field (check if all properties are None and return None).
            # However, we could be more efficient by checking if there are any other classes that use this class as a composite and are non-optional,
            # and eliminate the None check because we know that the class will always be re-created.
            cls_ast(
                stmt.LineBreak(),
                stmt.PythonDecoratorStatement(
                    expr.ExprFuncCall(expr.ExprIdent("classmethod"), [])
                ),
                lambda ast: ast.func(
                    "init_optional",
                    vars=init_optional_args,
                    return_type=PredefinedFn.item_getter(
                        ident_manager.use("Optional"), expr.ExprIdent(cls.name)
                    ),
                    comment="Create an embedded instance from the embedded columns in the database table. If all properties of this embedded class are None (indicating that the parent field is None), then this function will return None.",
                )(
                    lambda ast_l1: ast_l1.if_(
                        expr.ExprLogicalAnd(init_optional_null_condition)
                    )(lambda ast_l2: ast_l2.return_(expr.ExprConstant(None))),
                    lambda ast_l1: ast_l1.return_(
                        expr.ExprFuncCall(
                            expr.ExprIdent("cls"),
                            [
                                from_db_type_conversion(
                                    expr.ExprIdent(""),
                                    prop,
                                    expr.ExprIdent(get_python_property_name(prop)),
                                )
                                for prop in cls.properties.values()
                            ],
                        )
                    ),
                ),
                stmt.LineBreak(),
                lambda ast: ast.func(
                    "__composite_values__",
                    [
                        DeferredVar.simple("self"),
                    ],
                    return_type=expr.ExprIdent("tuple"),
                    comment="Return the values of the properties of this embedded class as a tuple. This is used to create a composite object in SQLAlchemy.",
                )(
                    lambda ast_l1: ast_l1.return_(
                        PredefinedFn.tuple(
                            [
                                to_db_type_conversion(
                                    program, expr.ExprIdent("self"), cls, "create", prop
                                )
                                for prop in cls.properties.values()
                            ]
                        )
                    )
                ),
            )

    def make_data_schema_export():
        program = Program()
        program.import_("__future__.annotations", True)

        expose_vars = [expr.ExprConstant(cls.name) for cls in schema.classes.values()]
        expose_vars.append(expr.ExprConstant("dataschema"))

        output = []
        for cls in schema.classes.values():
            program.import_(
                f"{target_pkg.path}.{cls.get_pymodule_name()}.{cls.name}",
                True,
            )
            output.append((expr.ExprConstant(cls.name), expr.ExprIdent(cls.name)))

        program.root(
            stmt.LineBreak(),
            lambda ast: ast.assign(
                DeferredVar.simple("dataschema"), PredefinedFn.dict(output)
            ),
            stmt.LineBreak(),
            lambda ast: ast.assign(
                DeferredVar.simple("__all__"),
                PredefinedFn.list(expose_vars),
            ),
        )

        target_pkg.parent().module("data_schema").write(program)

    for cls in schema.topological_sort():
        if cls.name in reference_classes:
            continue

        program = Program()
        make_create(program, cls)
        program.root.linebreak()
        make_update(program, cls)
        program.root.linebreak()
        make_normal(program, cls)
        target_pkg.module(cls.get_pymodule_name()).write(program)

    make_data_schema_export()


def get_data_conversion(
    source_pytype: str, target_pytype: str
) -> Callable[[expr.Expr], expr.Expr]:
    if source_pytype == target_pytype:
        return lambda x: x
    if source_pytype == "str" and target_pytype == "bytes":
        return lambda x: expr.ExprMethodCall(x, "encode", [])
    raise NotImplementedError(f"Cannot convert {source_pytype} to {target_pytype}")
