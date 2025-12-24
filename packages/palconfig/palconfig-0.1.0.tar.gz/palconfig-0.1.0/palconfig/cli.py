from __future__ import annotations

import argparse
import json
from pathlib import Path

from palconfig.codec import merge_old_into_new, parse_optionsettings, serialize_optionsettings
from palconfig.schema import schema_json


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(prog="palconfig", description="Convert/merge PalWorldSettings.ini OptionSettings <-> JSON.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_tojson = sub.add_parser("to-json", help="Convert INI to JSON")
    p_tojson.add_argument("--ini", type=Path, required=True)
    p_tojson.add_argument("--out", type=Path, required=True)
    p_tojson.add_argument("--indent", type=int, default=2)

    p_fromjson = sub.add_parser("from-json", help="Convert JSON to INI (OptionSettings line)")
    p_fromjson.add_argument("--json", type=Path, required=True)
    p_fromjson.add_argument("--out", type=Path, required=True)

    p_merge = sub.add_parser("merge", help="Merge old INI values into new INI defaults")
    p_merge.add_argument("--old", type=Path, required=True)
    p_merge.add_argument("--new", type=Path, required=True)
    p_merge.add_argument("--out-ini", type=Path, required=True)
    p_merge.add_argument("--out-json", type=Path, required=False)

    p_schema = sub.add_parser("schema", help="Generate JSON Schema from a reference INI")
    p_schema.add_argument("--ref-ini", type=Path, required=True)
    p_schema.add_argument("--out", type=Path, required=True)

    args = ap.parse_args()

    if args.cmd == "to-json":
        text = _read_text(args.ini)
        d, order = parse_optionsettings(text)
        payload = {
            "section": "/Script/Pal.PalGameWorldSettings",
            "option_settings": d,
            "order": order,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=args.indent, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0

    if args.cmd == "from-json":
        payload = json.loads(_read_text(args.json))
        d = payload["option_settings"]
        order = payload.get("order")
        ini = "[/Script/Pal.PalGameWorldSettings]\n" + serialize_optionsettings(d, order=order) + "\n"
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(ini, encoding="utf-8")
        return 0

    if args.cmd == "merge":
        old_text = _read_text(args.old)
        new_text = _read_text(args.new)
        res = merge_old_into_new(old_text, new_text)

        ini = "[/Script/Pal.PalGameWorldSettings]\n" + serialize_optionsettings(res.merged, order=res.order) + "\n"
        args.out_ini.parent.mkdir(parents=True, exist_ok=True)
        args.out_ini.write_text(ini, encoding="utf-8")

        if args.out_json:
            payload = {
                "section": "/Script/Pal.PalGameWorldSettings",
                "merged_option_settings": res.merged,
                "order": res.order,
                "deprecated_or_unknown_from_old": res.deprecated_or_unknown_from_old,
            }
            args.out_json.parent.mkdir(parents=True, exist_ok=True)
            args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        return 0

    if args.cmd == "schema":
        ref_text = _read_text(args.ref_ini)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(schema_json(ref_text), encoding="utf-8")
        return 0

    return 2
