"""Read raw flag files from disk and hand them to normalize_flags.

Two formats: JSON objects, and the plain `key=value` lines that format_flags
emits, so its output can be read back in. YAML is deliberately not handled;
the standard library has no parser for it.
"""

import json
from pathlib import Path

from .normalize import FlagFormatError, normalize_flags


def _reject_duplicates(pairs):
    # json.loads keeps the last of two identical keys, which is the same kind
    # of silent overwrite normalize_flags refuses to do for colliding keys.
    result = {}
    for key, value in pairs:
        if key in result:
            raise FlagFormatError(f"duplicate key {key!r} in JSON object")
        result[key] = value
    return result


def parse_json(text):
    """Parse JSON text holding a single top-level object into a raw dict."""
    try:
        data = json.loads(text, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as exc:
        raise FlagFormatError(f"invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise FlagFormatError(
            f"JSON flag file must hold an object, got {type(data).__name__}"
        )
    return data


def parse_lines(text):
    """Parse `key=value` lines into a raw dict.

    Blank lines and lines starting with '#' are skipped. Values stay strings;
    normalize_value decides what they mean. Splits on the first '=' only.
    """
    result = {}
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        key, sep, value = stripped.partition("=")
        if not sep:
            raise FlagFormatError(f"line {number}: expected key=value, got {line!r}")
        key = key.strip()
        if key in result:
            raise FlagFormatError(f"line {number}: duplicate key {key!r}")
        result[key] = value.strip()
    return result


def load_raw_flags(path):
    """Read a flag file into a raw, un-normalized dict, picking the parser by suffix."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        raise FlagFormatError(f"{path}: YAML is not supported, use JSON or key=value")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise FlagFormatError(f"{path}: not valid UTF-8: {exc}") from exc

    try:
        if suffix == ".json":
            return parse_json(text)
        return parse_lines(text)
    except FlagFormatError as exc:
        raise FlagFormatError(f"{path}: {exc}") from exc


def load_flags(path):
    """Load a flag file and return it normalized."""
    return normalize_flags(load_raw_flags(path))
