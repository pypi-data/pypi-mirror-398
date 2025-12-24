from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable


_SECTION_RE = re.compile(r"^\s*\[/Script/Pal\.PalGameWorldSettings\]\s*$", re.IGNORECASE)
_OPTION_START_RE = re.compile(r"OptionSettings\s*=\s*\(", re.IGNORECASE)


@dataclass(frozen=True)
class MergeResult:
    """Result of merging an old config onto a new config schema."""
    merged: dict[str, Any]
    deprecated_or_unknown_from_old: dict[str, Any]
    order: list[str]


def _split_top_level_csv(s: str) -> list[str]:
    """Split a CSV string, ignoring commas inside quotes and nested parentheses."""
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    in_quotes = False
    escape = False

    for ch in s:
        if escape:
            buf.append(ch)
            escape = False
            continue

        if ch == "\\" and in_quotes:
            buf.append(ch)
            escape = True
            continue

        if ch == '"':
            buf.append(ch)
            in_quotes = not in_quotes
            continue

        if not in_quotes:
            if ch == "(":
                depth += 1
                buf.append(ch)
                continue
            if ch == ")":
                depth = max(0, depth - 1)
                buf.append(ch)
                continue
            if ch == "," and depth == 0:
                item = "".join(buf).strip()
                if item:
                    out.append(item)
                buf.clear()
                continue

        buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw == "":
        return ""

    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1].replace('\\"', '"')

    if raw.lower() == "none":
        return None

    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False

    if raw.startswith("(") and raw.endswith(")"):
        inner = raw[1:-1].strip()
        if inner == "":
            return []
        return [_parse_value(p) for p in _split_top_level_csv(inner)]

    if re.fullmatch(r"[+-]?\d+", raw):
        try:
            return int(raw)
        except ValueError:
            return raw

    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\d*\.\d+)", raw):
        try:
            return float(raw)
        except ValueError:
            return raw

    return raw


def _encode_value(v: Any) -> str:
    if v is None:
        return "None"
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, list):
        return "(" + ",".join(_encode_value(x) for x in v) + ")"
    if isinstance(v, str):
        if v == "" or any(ch.isspace() for ch in v) or any(ch in v for ch in ['"', ",", "(", ")", ";", "="]):
            return '"' + v.replace('"', '\\"') + '"'
        return v
    return str(v)


def extract_optionsettings_blob(text: str) -> str:
    """
    Extract the inside of OptionSettings=(...) from the PalGameWorldSettings section.
    Returns the raw string inside the outermost parentheses.

    Raises:
      ValueError if not found or malformed.
    """
    section_header_re = re.compile(r"^\s*\[/Script/Pal\.PalGameWorldSettings\]\s*$", re.IGNORECASE | re.MULTILINE)
    any_section_re = re.compile(r"^\s*\[.*\]\s*$", re.MULTILINE)

    sec = section_header_re.search(text)
    if not sec:
        raise ValueError("Could not find [/Script/Pal.PalGameWorldSettings] section in text.")

    section_start = sec.end()

    nxt = any_section_re.search(text, pos=section_start)
    section_end = nxt.start() if nxt else len(text)

    section_text = text[section_start:section_end]

    opt = _OPTION_START_RE.search(section_text)
    if not opt:
        raise ValueError("Could not find OptionSettings=(...) in the PalGameWorldSettings section.")

    # Global index in the full text, positioned right after the opening '('
    i = section_start + opt.end()

    depth = 1
    in_quotes = False
    escape = False
    out: list[str] = []

    while i < len(text):
        ch = text[i]
        i += 1

        if escape:
            out.append(ch)
            escape = False
            continue

        if ch == "\\" and in_quotes:
            out.append(ch)
            escape = True
            continue

        if ch == '"':
            out.append(ch)
            in_quotes = not in_quotes
            continue

        if not in_quotes:
            if ch == "(":
                depth += 1
                out.append(ch)
                continue
            if ch == ")":
                depth -= 1
                if depth == 0:
                    return "".join(out).strip()
                out.append(ch)
                continue

        out.append(ch)

    raise ValueError("OptionSettings=(...) appears unterminated (missing closing ')').")

def parse_optionsettings(text: str) -> tuple[dict[str, Any], list[str]]:
    """
    Parse OptionSettings=(...) into a dict and an ordered key list (appearance order).
    """
    blob = extract_optionsettings_blob(text)
    items = _split_top_level_csv(blob)

    d: dict[str, Any] = {}
    order: list[str] = []

    for item in items:
        if "=" not in item:
            key = item.strip()
            if key:
                d[key] = True
                order.append(key)
            continue

        k, v = item.split("=", 1)
        key = k.strip()
        val = _parse_value(v.strip())
        d[key] = val
        order.append(key)

    return d, order


def serialize_optionsettings(d: dict[str, Any], order: Iterable[str] | None = None) -> str:
    """
    Serialize a dict back into OptionSettings=(...) format.

    If order is provided, keys are emitted in that order.
    Any keys not present in order are appended in sorted order.
    """
    if order is None:
        keys = sorted(d.keys())
        return "OptionSettings=(" + ",".join(f"{k}={_encode_value(d[k])}" for k in keys) + ")"

    order_list = list(order)
    used = set(order_list)
    remaining = sorted(k for k in d.keys() if k not in used)

    keys = [k for k in order_list if k in d] + remaining
    return "OptionSettings=(" + ",".join(f"{k}={_encode_value(d[k])}" for k in keys) + ")"


def merge_old_into_new(old_text: str, new_text: str) -> MergeResult:
    """
    Merge OLD config values into NEW defaults, keeping NEW's key set and ordering.

    - All NEW keys are present in merged.
    - OLD overrides NEW for matching keys.
    - OLD-only keys are returned separately as deprecated/unknown.
    """
    old_d, _old_order = parse_optionsettings(old_text)
    new_d, new_order = parse_optionsettings(new_text)

    merged = dict(new_d)
    for k, v in old_d.items():
        if k in new_d:
            merged[k] = v

    deprecated = {k: v for k, v in old_d.items() if k not in new_d}
    return MergeResult(merged=merged, deprecated_or_unknown_from_old=deprecated, order=new_order)
