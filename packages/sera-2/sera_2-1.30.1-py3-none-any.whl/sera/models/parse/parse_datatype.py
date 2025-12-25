from __future__ import annotations

import re
from copy import deepcopy

from sera.models._datatype import (
    DataType,
    PyTypeWithDep,
    SQLTypeWithDep,
    TsTypeWithDep,
    predefined_datatypes,
    predefined_py_datatypes,
    predefined_sql_datatypes,
    predefined_ts_datatypes,
)
from sera.models._schema import Schema


def parse_datatype(schema: Schema, datatype: dict | str) -> DataType:
    if isinstance(datatype, str):
        if datatype.endswith("[]"):
            datatype = datatype[:-2]
            is_list = True
        else:
            is_list = False

        if datatype.startswith("enum:"):
            enum_name = datatype[5:]
            if enum_name not in schema.enums:
                raise NotImplementedError("Unknown enum: " + enum_name)
            enum = schema.enums[enum_name]
            return DataType(
                # we can't set the correct dependency of this enum type because we do not know
                # the correct package yet.
                pytype=PyTypeWithDep(
                    type=enum.name,
                    deps=[
                        f"{schema.name}.models.enums.{enum.get_pymodule_name()}.{enum.name}"
                    ],
                ),
                sqltype=SQLTypeWithDep(
                    type=f"Enum({enum.name})",
                    mapped_pytype=enum.name,
                    deps=[
                        "sqlalchemy.Enum",
                        f"{schema.name}.models.enums.{enum.get_pymodule_name()}.{enum.name}",
                    ],
                ),
                tstype=TsTypeWithDep(
                    type=enum.name,
                    spectype=enum.name,
                    deps=[f"@.models.enums.{enum.name}"],
                ),
                is_list=is_list,
            )

        if datatype not in predefined_datatypes:
            raise NotImplementedError(datatype)

        dt = deepcopy(predefined_datatypes[datatype])
        dt.is_list = is_list
        return dt
    if isinstance(datatype, dict):
        is_list = datatype.get("is_list", False)

        # Parse Python type and argument if present
        if datatype["pytype"] in predefined_py_datatypes:
            py_type = predefined_py_datatypes[datatype["pytype"]]
        else:
            py_type = PyTypeWithDep(
                type=datatype["pytype"]["type"], deps=datatype["pytype"].get("deps", [])
            )

        # Parse SQL type and argument if present
        m = re.match(r"^([a-zA-Z0-9_]+)(\([^)]+\))?$", datatype["sqltype"])
        if m is not None:
            sql_type_name = m.group(1)
            sql_type_arg = m.group(2)
            # Use the extracted type to get the predefined SQL type
            if sql_type_name not in predefined_sql_datatypes:
                raise NotImplementedError(sql_type_name)
            sql_type = predefined_sql_datatypes[sql_type_name]
            if sql_type_arg is not None:
                # process the argument
                sql_type.type = sql_type.type + sql_type_arg
        else:
            raise ValueError(f"Invalid SQL type format: {datatype['sqltype']}")

        return DataType(
            pytype=py_type,
            sqltype=sql_type,
            tstype=predefined_ts_datatypes[datatype["tstype"]],
            is_list=is_list,
        )

    raise NotImplementedError(datatype)
