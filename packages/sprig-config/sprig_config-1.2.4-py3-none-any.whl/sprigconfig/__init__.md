# sprigconfig/__init__.py — Public API Documentation

This document explains the purpose, design goals, and expected behavior of the `sprigconfig.__init__` module.  
It corresponds directly to the source file:

```
sprigconfig/__init__.py
```

---

## Purpose

The `sprigconfig.__init__` module defines the **public API surface** of the SprigConfig package.  
Only stable, supported, externally consumable classes and functions are exported here.

Anything *not* listed in `__all__` is treated as **internal**, meaning its behavior may change without notice.

---

## Public API Exports

### 1. `Config`
A wrapper around deeply nested dictionaries that provides:

- dict-like access  
- dotted-key lookup (`cfg.get("a.b.c")`)  
- safe serialization  
- automatic wrapping of nested dicts into `Config`

This is the primary runtime config object returned by all loading mechanisms.

---

### 2. `ConfigLoader`
The main config-loading engine.  
Responsibilities include:

- Reading YAML files  
- Applying profile overlays  
- Resolving imports  
- Performing deep merges  
- Injecting runtime metadata under `sprigconfig._meta`

All new functionality flows through `ConfigLoader`.

---

### 3. `ConfigSingleton`
A thread-safe, Java-style configuration cache used by components that want a single global config instance.

Key capabilities:

- `initialize(profile, config_dir)`  
- `get()`  
- `reload_for_testing()`  
- `_clear_all()` (test-only)

It is fully optional—projects may use `load_config()` instead.

---

### 4. `deep_merge`
A standalone dictionary merge helper.  
Maintained for backward compatibility with older ETL-service code.

- Deep, recursive  
- Lists overwrite, not append  
- Behaves exactly as older versions did

---

### 5. `ConfigLoadError`
The canonical exception type for *all* config loader errors.

Raised for:

- Missing or invalid YAML  
- Circular imports  
- Failed secrets decryption  
- Invalid profile usage  
- Singleton misuse

---

### 6. `load_config()`
The **legacy API**, preserved to avoid breaking older code.

```python
cfg = load_config(profile="dev", config_dir="/path/to/config")
```

Behavior:

- Delegates internally to `ConfigLoader`  
- Always returns a `Config` instance (never a raw dict)  
- Raises `ConfigLoadError` if something unexpected happens  
- Fully backward compatible  

This ensures existing ETL-service-web code continues to work unchanged.

---

## Backward Compatibility Guarantees

This module explicitly protects older integrations by ensuring:

### ✔ Import patterns still work:
```python
from sprigconfig import load_config, deep_merge
```

### ✔ `load_config()` returns a mapping-like object  
Even though the object is now a `Config`, not a raw dictionary.

### ✔ `deep_merge()` remains stable  
No behavioral changes were introduced in RC3.

---

## Design Principles Reflected in `__init__`

1. **Explicit public API**  
   Only documented and intentionally supported interfaces appear in `__all__`.

2. **Stable surface, flexible internals**  
   Internal refactoring does not affect consuming code.

3. **Clear upgrade path**  
   New projects should use `ConfigLoader` directly; old projects may continue using `load_config()`.

4. **Runtime safety**  
   Defensive check ensures loader always returns a `Config`.

---

## `__all__` Reference

```
__all__ = [
    "Config",
    "ConfigLoader",
    "ConfigSingleton",
    "deep_merge",
    "ConfigLoadError",
    "load_config",
]
```

If it isn’t in this list, it is *not* part of the public API.

---

# Summary

The `sprigconfig.__init__` module acts as the official boundary of SprigConfig’s public interface.  
It guarantees compatibility for old codebases while enabling newer, more powerful features through `ConfigLoader`, `Config`, and `ConfigSingleton`.

It ensures that SprigConfig remains:

- predictable  
- stable  
- backward compatible  
- safe for long-term enterprise use  

---

If you want, I can generate matching API docs for the rest of the package (ConfigLoader, Config, Singleton, deep_merge), or assemble everything into a single combined PDF or MD manual.
