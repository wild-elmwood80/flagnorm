# flagnorm

Feature flag config accumulates mess. One service writes `new-checkout-flow`,
another writes `new_checkout.flow`, a config file from two years ago has
`Feature Flag` with a space in it, and the boolean values are a mix of
`"true"`, `"1"`, `"yes"`, `"on"`, and actual booleans depending on who typed
them in and when. Two keys that were meant to be the same flag can quietly
drift apart, or a value someone assumed was falsy turns out to be a string
that nothing actually parses as `False`.

flagnorm takes a dict of raw flag keys and values and normalizes it into one
canonical form: snake_case keys, real booleans, and a loud error instead of a
silent guess when something doesn't parse cleanly.

## Usage

```python
from flagnorm import normalize_flags, format_flags, FlagFormatError

raw = {
    "Feature-Flag": "yes",
    "new_checkout.flow": "0",
    "  Dark Mode  ": True,
}

normalize_flags(raw)
# {'feature_flag': True, 'new_checkout_flow': False, 'dark_mode': True}

print(format_flags(raw))
# dark_mode=true
# feature_flag=true
# new_checkout_flow=false
```

Bad input raises `FlagFormatError` instead of guessing:

```python
try:
    normalize_flags({"feature-flag": "true", "feature_flag": "false"})
except FlagFormatError as exc:
    print(exc)
    # flag keys 'feature-flag' and 'feature_flag' both normalize to 'feature_flag'
```

## Rules

- Keys: lowercased, `-`, `.`, `/`, and whitespace all fold to `_`, repeated
  separators collapse, leading/trailing separators are stripped. What's left
  must look like a plain identifier (`^[a-z][a-z0-9_]*$`) or it's rejected.
- Values: real `bool`s pass through. Strings are matched case-insensitively
  against known spellings (`true`/`t`/`yes`/`y`/`on`/`enabled`/`1` and their
  opposites). Anything else - `"maybe"`, `"2"`, `None`, a list - is rejected.
- Two raw keys that normalize to the same canonical key is treated as an
  error, not a silent overwrite, since that almost always means two names
  for the same flag have drifted apart somewhere upstream.

## Loading files

```python
from flagnorm import load_flags

load_flags("flags.json")   # top-level JSON object
load_flags("flags.conf")   # key=value lines, '#' comments allowed
```

The parser is picked by file suffix: `.json` is JSON, anything else is read as
`key=value` lines (the same shape `format_flags` prints). Duplicate keys in
the file are an error, not last-one-wins. `.yaml`/`.yml` files are refused
because the standard library can't parse YAML and this project has no
dependencies. `load_raw_flags` returns the dict before normalization.

## Status

Early. Dict-in, dict-out normalization with a table-driven test suite for the
awkward cases, plus JSON and key=value file loading. No CLI yet.

## Running the tests

```
python -m unittest discover tests
```
