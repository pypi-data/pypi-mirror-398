from __future__ import annotations

from sera.models._enum import Enum, EnumValue
from sera.models._multi_lingual_string import MultiLingualString
from sera.models._schema import Schema
from sera.models.parse.parse_utils import parse_multi_lingual_string


def parse_enum(schema: Schema, enum_name: str, enum: dict) -> Enum:
    values = {}
    for k, v in enum.items():
        if isinstance(v, (str, int)):
            values[k] = EnumValue(
                name=k,
                value=v,
                label=MultiLingualString.en(""),
                description=MultiLingualString.en(""),
            )
        else:
            try:
                values[k] = EnumValue(
                    name=k,
                    value=v["value"],
                    label=parse_multi_lingual_string(v.get("label", "")),
                    description=parse_multi_lingual_string(v.get("desc", "")),
                )
            except KeyError as e:
                raise ValueError(f"Invalid enum value definition for {k}: {v}") from e
    return Enum(name=enum_name, values=values)
