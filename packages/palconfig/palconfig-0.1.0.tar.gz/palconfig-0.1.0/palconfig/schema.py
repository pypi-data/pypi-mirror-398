from __future__ import annotations

import json
from typing import Any

from palconfig.codec import parse_optionsettings


def _type_union(schema: dict[str, Any]) -> list[str]:
    t = schema.get("type")
    if isinstance(t, list):
        return list(t)
    if isinstance(t, str):
        return [t]
    return []


def _schema_for_value(v: Any) -> dict[str, Any]:
    if v is None:
        return {"type": ["null", "string", "number", "boolean", "array", "object"]}

    if isinstance(v, bool):
        return {"type": "boolean"}

    if isinstance(v, int):
        return {"type": "integer"}

    if isinstance(v, float):
        return {"type": "number"}

    if isinstance(v, str):
        return {"type": "string"}

    if isinstance(v, list):
        if not v:
            return {"type": "array", "items": {"type": ["string", "number", "boolean", "null", "array", "object"]}}

        types: set[str] = set()
        for item in v:
            for t in _type_union(_schema_for_value(item)):
                types.add(t)

        return {"type": "array", "items": {"type": sorted(types)}}

    return {"type": ["string", "number", "boolean", "null", "array", "object"]}


def build_optionsettings_schema(reference_ini_text: str) -> dict[str, Any]:
    """
    Build a JSON Schema (Draft 2020-12) based on a reference INI file.

    The schema is strict about known keys (additionalProperties: false) and
    sets types based on parsed values in the reference.
    """
    ref_dict, order = parse_optionsettings(reference_ini_text)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Palworld OptionSettings",
        "type": "object",
        "additionalProperties": False,
        "properties": {k: _schema_for_value(ref_dict[k]) for k in order},
        "required": list(order),
    }
    return schema


def schema_json(reference_ini_text: str, indent: int = 2) -> str:
    return json.dumps(build_optionsettings_schema(reference_ini_text), indent=indent, ensure_ascii=False) + "\n"
