from __future__ import annotations

from sera.models._class import Class
from sera.models._constraints import Constraint, predefined_constraints
from sera.models._property import (
    Cardinality,
    DataPropDBInfo,
    DataProperty,
    ForeignKeyOnDelete,
    ForeignKeyOnUpdate,
    IndexType,
    ObjectPropDBInfo,
    ObjectProperty,
    PropDataAttrs,
)
from sera.models._schema import Schema
from sera.models.parse.parse_datatype import parse_datatype
from sera.models.parse.parse_system_controlled import parse_system_controlled_attrs
from sera.models.parse.parse_utils import (
    parse_default_factory,
    parse_default_value,
    parse_multi_lingual_string,
)
from sera.typing import UNSET


def parse_property(
    schema: Schema, owner: Class, prop_name: str, prop: dict
) -> DataProperty | ObjectProperty:
    if isinstance(prop, str):
        # deprecated
        assert False, prop

    db = prop.get("db", {})
    _data = prop.get("data", {})
    data_attrs = PropDataAttrs(
        is_private=_data.get("is_private", False),
        datatype=(
            parse_datatype(schema, _data["datatype"]) if "datatype" in _data else None
        ),
        constraints=[
            parse_constraint(constraint) for constraint in _data.get("constraints", [])
        ],
        system_controlled=parse_system_controlled_attrs(_data.get("system_controlled")),
        default_value=UNSET if "default_value" not in _data else _data["default_value"],
    )

    assert isinstance(prop, dict), prop
    if "datatype" in prop:
        return_prop = DataProperty(
            owner=owner,
            name=prop_name,
            label=parse_multi_lingual_string(prop.get("label", prop_name)),
            description=parse_multi_lingual_string(prop.get("desc", "")),
            datatype=parse_datatype(schema, prop["datatype"]),
            data=data_attrs,
            db=(
                DataPropDBInfo(
                    is_primary_key=db.get("is_primary_key", False),
                    is_auto_increment=db.get("is_auto_increment", False),
                    is_unique=db.get("is_unique", False),
                    is_indexed=db.get("is_indexed", False)
                    or db.get("is_unique", False)
                    or db.get("is_primary_key", False),
                    index_type=(
                        IndexType(db["index_type"]) if "index_type" in db else None
                    ),
                    foreign_key=schema.classes.get(db.get("foreign_key")),
                )
                if "db" in prop
                else None
            ),
            is_optional=prop.get("is_optional", False),
            default_value=parse_default_value(prop.get("default_value", None)),
            default_factory=parse_default_factory(prop.get("default_factory", None)),
        )
        if return_prop.db is not None and return_prop.db.is_indexed:
            if return_prop.db.index_type is None:
                return_prop.db.index_type = IndexType.DEFAULT
        return return_prop

    assert "target" in prop, prop
    return ObjectProperty(
        owner=owner,
        name=prop_name,
        label=parse_multi_lingual_string(prop.get("label", prop_name)),
        description=parse_multi_lingual_string(prop.get("desc", "")),
        target=schema.classes[prop["target"]],
        cardinality=Cardinality(prop.get("cardinality", "1:1")),
        is_optional=prop.get("is_optional", False),
        data=data_attrs,
        db=(
            ObjectPropDBInfo(
                is_embedded=db.get("is_embedded", None),
                on_target_delete=ForeignKeyOnDelete(
                    db.get("on_target_delete", "restrict")
                ),
                on_target_update=ForeignKeyOnUpdate(
                    db.get("on_target_update", "restrict")
                ),
                on_source_delete=ForeignKeyOnDelete(
                    db.get("on_source_delete", "restrict")
                ),
                on_source_update=ForeignKeyOnUpdate(
                    db.get("on_source_update", "restrict")
                ),
            )
            if "db" in prop
            else None
        ),
    )


def parse_constraint(constraint: str) -> Constraint:
    if constraint not in predefined_constraints:
        raise NotImplementedError(constraint)
    return predefined_constraints[constraint]
