# config.md

Documentation for `sprigconfig/config.py`.

## Overview

`Config` is the core immutable-ish mapping wrapper used throughout SprigConfig.  
It provides:

- Dict-like behavior (`keys`, `items`, iteration, containment)
- Deep recursive wrapping of nested dictionaries
- Dotted-key lookup (`cfg["a.b.c"]` or `cfg.get("a.b.c")`)
- Safe conversion to plain dictionaries with optional secret redaction
- YAML dumping with optional pretty-printing and secret handling

---

## Class: `Config`

### ### Initialization

```python
cfg = Config(data: dict)
```

- Must wrap a `dict`; otherwise `TypeError` is raised.
- All nested dicts and lists are recursively wrapped.

---

## Internal Wrapping

`_wrap(obj)` recursively converts:

- dict → `{k: Config-wrapped-value}`
- list → `[wrapped values]`
- Config → returned unchanged
- primitive → returned unchanged

This ensures consistency so that any nested dict automatically becomes a `Config`.

---

## Mapping Behavior

### `__getitem__(key)`
Supports:
- `cfg["a.b.c"]` (dotted key lookup)
- `cfg["a"]["b"]["c"]` (nested access)
- Raises `KeyError` if any part is missing.

When the resolved value is a dict, a new `Config` instance is returned.

### `__contains__(key)`
Returns `True` if the dotted key or normal key resolves.

### `__len__` / `__iter__`
Standard mapping behavior.

---

## Dotted-Key Access

### `get(key, default=None)`

- Resolves dotted paths (“a.b.c”)
- Returns `default` if missing
- Returns nested `Config` for dict nodes

Example:

```python
cfg.get("etl.jobs.root")
```

---

## Serialization: `to_dict()`

```python
cfg.to_dict(reveal_secrets=False)
```

Produces a deep plain-Python dictionary.

Secret handling:

- If `reveal_secrets=False`:  
  LazySecret → `"<LazySecret>"`
- If `reveal_secrets=True`:  
  Decrypts via `LazySecret.get()` or raises `ConfigLoadError` if decryption fails.

---

## YAML Dumping

### `dump(path=None, safe=True, pretty=True, sprigconfig_first=False)`

- `path=None`: returns YAML string
- `path=Path`: writes YAML to file
- `safe=True`: redact LazySecret values
- `safe=False`: reveal secrets (unsafe) or raise on failure
- `pretty=True`: block-style YAML
- `sprigconfig_first=True`: reorder `"sprigconfig"` key to appear first

---

## Error Handling

### `ConfigLoadError`
Raised when:
- secrets cannot be decrypted during unsafe output
- dump-to-file fails

---

## Representation

`__repr__` shows the internal wrapped structure for debugging.

---

## Summary

`Config` is a lightweight but powerful immutable configuration wrapper enabling:

- Protected config state
- Human-friendly dotted-key access
- Secure serialization
- Optional redaction of secrets
- Safe, structured YAML output

It is one of the core building blocks for SprigConfig’s loading pipeline.

