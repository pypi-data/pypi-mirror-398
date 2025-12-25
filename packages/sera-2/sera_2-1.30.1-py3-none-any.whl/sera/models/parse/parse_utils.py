from __future__ import annotations

from sera.models._default import DefaultFactory
from sera.models._multi_lingual_string import MultiLingualString


def parse_multi_lingual_string(o: dict | str) -> MultiLingualString:
    if isinstance(o, str):
        return MultiLingualString.en(o)
    assert isinstance(o, dict), o
    assert "en" in o
    return MultiLingualString(lang2value=o, lang="en")


def parse_default_value(
    default_value: str | int | bool | None,
) -> str | int | bool | None:
    if default_value is None:
        return None
    if not isinstance(default_value, (str, int, bool)):
        raise NotImplementedError(default_value)
    return default_value


def parse_default_factory(default_factory: dict | None) -> DefaultFactory | None:
    if default_factory is None:
        return None
    return DefaultFactory(
        pyfunc=default_factory["pyfunc"], tsfunc=default_factory["tsfunc"]
    )
