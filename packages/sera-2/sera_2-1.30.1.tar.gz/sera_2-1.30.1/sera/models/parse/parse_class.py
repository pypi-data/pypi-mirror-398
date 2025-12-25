from __future__ import annotations

from sera.models._class import Class, ClassDBMapInfo, Index
from sera.models._schema import Schema
from sera.models.parse.parse_utils import parse_multi_lingual_string


def parse_class_without_prop(schema: Schema, clsname: str, cls: dict) -> Class:
    db = None
    if "db" in cls:
        indices = []
        for idx in cls["db"].get("indices", []):
            index = Index(
                name=idx.get("name", "_".join(idx["columns"]) + "_index"),
                columns=idx["columns"],
                unique=idx.get("unique", False),
            )
            indices.append(index)
        db = ClassDBMapInfo(table_name=cls["db"]["table_name"], indices=indices)

    return Class(
        name=clsname,
        label=parse_multi_lingual_string(cls["label"]),
        description=parse_multi_lingual_string(cls.get("desc", "")),
        properties={},
        db=db,
        events=[],
    )
