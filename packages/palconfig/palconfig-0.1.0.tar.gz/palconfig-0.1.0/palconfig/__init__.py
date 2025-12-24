"""
palconfig

Library:
  - Parse PalWorldSettings.ini OptionSettings=(...) blobs to dict
  - Serialize dict back to OptionSettings=(...)
  - Merge old config onto new defaults
  - Produce a JSON Schema from a reference config
"""

from .codec import (
    extract_optionsettings_blob,
    parse_optionsettings,
    serialize_optionsettings,
    merge_old_into_new,
)

__all__ = [
    "extract_optionsettings_blob",
    "parse_optionsettings",
    "serialize_optionsettings",
    "merge_old_into_new",
]
