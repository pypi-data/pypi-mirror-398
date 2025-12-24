# PalConfig

Utilities for parsing, merging, and serializing Palworld `PalWorldSettings.ini` config files.

This package focuses on:

- **INI ➜ JSON** conversion (lossless for values; preserves key order)
- **JSON ➜ INI** conversion (emits `OptionSettings=(...)`)
- **Merge**: apply an *old* config onto a *new* default schema (new keys kept, old values override matching keys)
- **JSON Schema** generation from a reference config

> Palworld uses an Unreal Engine-ish config format where most server settings live inside a single `OptionSettings=(...)` tuple.
> `palconfig` treats that tuple as the source of truth.

---

## Install

### Poetry (recommended)

```bash
poetry add palconfig
```

### Editable install (local dev)

```bash
poetry install
```

---

## CLI

Once installed, you get the `palconfig` command.

### Merge old values into new defaults (recommended workflow)

```bash
palconfig merge --old Old.ini --new New.ini --out-ini PalWorldSettings.ini --out-json merged.json
```

- Output INI contains the **new schema** + your **old tuned values**
- `merged.json` (optional) includes:
  - `merged_option_settings`
  - `deprecated_or_unknown_from_old` (keys that existed only in old)

### Convert INI ➜ JSON

```bash
palconfig to-json --ini PalWorldSettings.ini --out settings.json
```

Output JSON shape:

```json
{
  "section": "/Script/Pal.PalGameWorldSettings",
  "option_settings": {
    "ExpRate": 5.0,
    "ServerName": "Tectonix GX S4",
    "CrossplayPlatforms": ["Steam", "Xbox", "PS5", "Mac"]
  },
  "order": ["ExpRate", "ServerName", "CrossplayPlatforms"]
}
```

### Convert JSON ➜ INI

```bash
palconfig from-json --json settings.json --out PalWorldSettings.ini
```

This emits:

- `[/Script/Pal.PalGameWorldSettings]`
- A single `OptionSettings=(...)` line

### Generate JSON Schema (from a reference INI)

```bash
palconfig schema --ref-ini NewDefaults.ini --out optionsettings.schema.json
```

Notes:

- The schema is generated from the parsed values in the reference file.
- It is **strict** about keys: `additionalProperties: false`
- Types are inferred (bool/int/float/string/array). Empty lists default to permissive item types.

---

## Library usage

```python
from palconfig.codec import (
    parse_optionsettings,
    serialize_optionsettings,
    merge_old_into_new,
)

old_text = open("Old.ini", "r", encoding="utf-8").read()
new_text = open("New.ini", "r", encoding="utf-8").read()

result = merge_old_into_new(old_text, new_text)

merged_ini = "[/Script/Pal.PalGameWorldSettings]\\n" + serialize_optionsettings(result.merged, order=result.order) + "\\n"
open("PalWorldSettings.ini", "w", encoding="utf-8").write(merged_ini)

print("Deprecated/unknown keys from old:", result.deprecated_or_unknown_from_old)
```

---

## Parsing rules

`palconfig` aims to match Palworld’s format as it appears in real configs:

- `None` ➜ `null` in JSON
- `True`/`False` ➜ booleans
- Numbers:
  - `8211` ➜ int
  - `1.000000` ➜ float
- Quoted strings:
  - `ServerName="Default Palworld Server"` ➜ `"Default Palworld Server"`
- Tuple lists:
  - `CrossplayPlatforms=(Steam,Xbox,PS5,Mac)` ➜ `["Steam","Xbox","PS5","Mac"]`
- Empty assignment:
  - `DenyTechnologyList=` ➜ `""`

Commas inside quotes and commas inside nested tuples are handled correctly.

---

## Merge behavior

When you run `palconfig merge`:

- All **NEW** keys are present in the merged output.
- If **OLD** has the same key, **OLD overrides NEW** (even if the old value is empty).
- Keys present only in **OLD** are captured in `deprecated_or_unknown_from_old`.

This keeps you aligned with upstream defaults while preserving your custom tuning.

---

## Testing

```bash
poetry run pytest
```

The test suite covers:

- basic type parsing (None/bool/int/float/string)
- nested tuple parsing
- round-trip stability (INI ➜ JSON ➜ INI ➜ JSON)
- merge semantics + ordering
- schema generation shape

---

## Practical safety note

Palworld configs often contain credentials (e.g., `AdminPassword`, `ServerPassword`).
If you're converting configs to JSON and sharing them, redact first — your future self will thank you.

---

## License

MIT

