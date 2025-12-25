# sprigconfig/deepmerge.py — Explanation and Purpose

This document describes the purpose, behavior, design rationale, and rules behind the `deep_merge` function used throughout SprigConfig.  
It is one of the core utilities that makes hierarchical configuration loading predictable, transparent, and safe.

---

## 1. What `deep_merge` Is For

SprigConfig loads configuration from multiple YAML files:

- `application.yml`  
- `application-<profile>.yml` overlays  
- Imported YAML files  
- Optional user overrides

All these files must be **merged** into one coherent configuration dictionary.

Python's built‑in `dict.update()` is not sufficient because it:

- Performs only a shallow merge  
- Overwrites entire nested dictionaries  
- Cannot detect missing partial overrides  
- Provides no logging visibility  

`deep_merge` implements a **canonical**, deterministic, production-safe deep merge algorithm.

---

## 2. Key Design Goals

### ✔ Predictable Merge Semantics  
The same inputs always produce the same merged configuration.

### ✔ Transparency  
Logs explicitly show:
- New keys added  
- Keys overridden  
- Partial overrides (missing keys)  

### ✔ Isolation  
`deep_merge` contains **no SprigConfig-specific logic**, so it:
- Can be unit-tested independently  
- Can be reused by external projects  
- Remains easy to reason about

### ✔ Safe Overrides  
Warns developers when an override file does *not* include keys found in the base file. This prevents accidental partial deletion unless explicitly suppressed.

---

## 3. The Merge Rules

These rules define exactly how configuration structures resolve when multiple sources merge.

### **Rule 1 — Dict + Dict → Recursive merge**
If both base and override values are dictionaries:

- Merge key-by-key  
- Recurse deeper  
- Warn if the override dictionary is missing keys present in the base  

This ensures overlays must be explicit unless warning suppression is enabled.

---

### **Rule 2 — List + List → Override, never append**
Lists do **not** merge element‑by‑element.

Example:

```yaml
base:
  ports: [8000, 8001]

override:
  ports: [9000]
```

Result:

```yaml
ports: [9000]
```

Appending would introduce order ambiguity and non-determinism, so SprigConfig replaces lists entirely.

---

### **Rule 3 — Scalar → Replace**
Integers, strings, booleans, floats, etc. are always overwritten.

---

### **Rule 4 — Missing Key → Add**
If a key exists in the override but not in base, it is added:

Logged as:

```
Adding new config 'path.to.key'
```

---

### **Rule 5 — Existing Key Overwrite → Log**
If a key exists in both base and override and values differ, the override wins.

Logged as:

```
Overriding config 'path.to.key'
```

---

### **Rule 6 — Missing Keys in Override → Warn**
If base has keys that override *does not* include:

Example:

```yaml
base:
  db:
    host: localhost
    port: 5432
    user: admin

override:
  db:
    host: service-db
```

Log warning:

```
Config section 'db' partially overridden; missing keys: {'port', 'user'}
```

This is extremely useful for catching accidental incomplete overrides.

Warnings can be suppressed during:

- Import-heavy configurations  
- Tests where noise is undesirable  
- Environments where missing keys are expected  

---

## 4. Runtime Behavior

### Function signature

```python
deep_merge(base, override, suppress=False, path="")
```

- **`base`** is mutated in-place  
- **`override`** dictates the changes  
- **`suppress=True`** disables all logging/warnings  
- **`path`** keeps track of nested keys for readable logging

Returns the modified base dictionary to allow chaining.

---

## 5. Why It Lives in Its Own Module

The deep merge algorithm must remain:

- Stable
- Reusable
- Easy to test
- Free from circular imports
- Independent of SprigConfig’s higher-level components

`ConfigLoader` depends on this function, but `deepmerge` depends on nothing in return.

This separation ensures a clean architecture consistent with SprigConfig’s design goals.

---

## 6. Example Merge

### Base

```yaml
server:
  host: 0.0.0.0
  port: 8080
  ssl:
    enabled: false
    ciphers: ["TLS_AES"]
```

### Override

```yaml
server:
  port: 9090
  ssl:
    enabled: true
```

### Result

```yaml
server:
  host: 0.0.0.0
  port: 9090
  ssl:
    enabled: true
    ciphers: ["TLS_AES"]
```

Note that `ciphers` stays untouched because the override did not specify it — and a warning is logged.

---

## 7. Summary

`deep_merge` is a critical part of SprigConfig’s configuration logic.  
It ensures:

- Deterministic merging  
- Clear logs and warnings  
- Protection from accidental partial overrides  
- Strong guarantees about final configuration correctness  

Because configuration is security‑critical and controls application behavior, the merge algorithm must be correct, transparent, and predictable — which is exactly what `deep_merge` provides.

---

