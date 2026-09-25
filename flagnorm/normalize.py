"""Normalize feature flag keys and values from messy, hand-edited sources."""

import re

_KEY_SEPARATORS = re.compile(r"[-.\s/]+")
_REPEAT_UNDERSCORE = re.compile(r"_+")
_VALID_KEY = re.compile(r"^[a-z][a-z0-9_]*$")

# Written by different people in different config files over the years.
_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off", "disabled"}


class FlagFormatError(ValueError):
    """Raised when a flag key or value cannot be normalized safely."""


def normalize_key(raw):
    """Turn a raw flag key into its canonical snake_case form.

    Accepts the usual mess: "Feature-Flag", "feature.flag", "  feature flag  ",
    "feature__flag". Refuses to guess when the result would be empty or would
    not read as a plain identifier (leading digit, stray punctuation), since a
    flag key that silently changes shape is worse than one that errors loudly.
    """
    if not isinstance(raw, str):
        raise FlagFormatError(f"flag key must be a string, got {type(raw).__name__}")

    key = raw.strip().lower()
    key = _KEY_SEPARATORS.sub("_", key)
    key = _REPEAT_UNDERSCORE.sub("_", key)
    key = key.strip("_")

    if not key:
        raise FlagFormatError(f"flag key {raw!r} normalizes to an empty string")
    if not _VALID_KEY.match(key):
        raise FlagFormatError(f"flag key {raw!r} normalizes to invalid identifier {key!r}")

    return key


def normalize_value(raw):
    """Coerce a raw flag value into a bool.

    Bools pass through untouched. Strings are matched case-insensitively
    against the known truthy/falsy spellings people actually type by hand.
    Anything else (numbers other than 0/1, lists, None, empty strings) is
    rejected rather than guessed at, since a wrong guess here flips a flag.
    """
    if isinstance(raw, bool):
        return raw

    if isinstance(raw, str):
        text = raw.strip().lower()
        if text in _TRUE_VALUES:
            return True
        if text in _FALSE_VALUES:
            return False
        raise FlagFormatError(f"flag value {raw!r} is not a recognized boolean spelling")

    raise FlagFormatError(f"flag value must be a bool or string, got {type(raw).__name__}")


def normalize_flags(raw):
    """Normalize a dict of raw flag key/value pairs into canonical form.

    Raises on any single bad key or value, and on collisions where two
    different raw keys normalize to the same canonical key - that almost
    always means two names for the same flag drifted apart, and silently
    picking one would hide the bug instead of surfacing it.
    """
    result = {}
    origins = {}

    for raw_key, raw_value in raw.items():
        key = normalize_key(raw_key)
        value = normalize_value(raw_value)

        if key in result:
            raise FlagFormatError(
                f"flag keys {origins[key]!r} and {raw_key!r} both normalize to {key!r}"
            )

        result[key] = value
        origins[key] = raw_key

    return result


def format_flags(raw):
    """Render a raw flags dict as sorted, canonical 'key=true/false' lines."""
    normalized = normalize_flags(raw)
    lines = [f"{key}={'true' if value else 'false'}" for key, value in sorted(normalized.items())]
    return "\n".join(lines)
