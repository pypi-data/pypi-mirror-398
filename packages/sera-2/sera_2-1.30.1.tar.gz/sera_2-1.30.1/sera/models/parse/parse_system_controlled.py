from __future__ import annotations

import orjson

from sera.models._property import GetSCPropValueFunc, SystemControlledAttrs


def parse_system_controlled_attrs(
    attrs: dict | None,
) -> SystemControlledAttrs | None:
    if attrs is None:
        return None
    if not isinstance(attrs, dict):
        raise NotImplementedError(attrs)

    if "on_upsert" in attrs:
        attrs = attrs.copy()
        attrs.update(
            {
                "on_create": attrs["on_upsert"],
                "on_create_bypass": attrs.get("on_upsert_bypass"),
                "on_update": attrs["on_upsert"],
                "on_update_bypass": attrs.get("on_upsert_bypass"),
            }
        )

    if "on_create" not in attrs or "on_update" not in attrs:
        raise ValueError(
            "System controlled attributes must have 'on_create', 'on_update', or 'on_upsert' must be defined."
        )

    if "on_search" in attrs:
        attrs.update(
            {
                "on_search": attrs["on_search"],
                "on_search_bypass": attrs.get("on_search_bypass"),
            }
        )

    keys = {}
    for key in ["on_create", "on_update", "on_search"]:
        if key not in attrs:
            continue

        if attrs[key] == "ignored":
            keys[key] = "ignored"
        elif attrs[key].find(":") != -1:
            func, args = attrs[key].split(":")
            assert func == "getattr", f"Unsupported function: {func}"
            args = orjson.loads(args)
            keys[key] = GetSCPropValueFunc(
                func=func,
                args=args,
            )
        else:
            raise ValueError(
                f"System controlled attribute '{key}' must be 'ignored' or a function call in the format '<funcname>:<args>'."
            )

        if attrs[key + "_bypass"] is not None:
            if not isinstance(attrs[key + "_bypass"], str):
                raise ValueError(
                    f"System controlled attribute '{key}_bypass' must be a string."
                )
            keys[key + "_bypass"] = attrs[key + "_bypass"]

    return SystemControlledAttrs(
        on_create=keys["on_create"],
        on_create_bypass=keys.get("on_create_bypass"),
        on_update=keys["on_update"],
        on_update_bypass=keys.get("on_update_bypass"),
        on_search=keys.get("on_search", "ignored"),
        on_search_bypass=keys.get("on_search_bypass"),
    )
