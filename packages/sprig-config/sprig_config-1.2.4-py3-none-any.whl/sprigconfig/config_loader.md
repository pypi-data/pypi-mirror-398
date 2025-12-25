# sprigconfig/config_loader.py — Explanation and Purpose

This document explains the purpose, design, and behavior of `ConfigLoader`, the core configuration-loading engine for **SprigConfig**.

`ConfigLoader` is responsible for turning a directory of configuration files into a single, deeply-merged, environment-aware, import-traceable configuration object.

---

## 1. What `ConfigLoader` Is For

SprigConfig aims to reproduce the power and ergonomics of Spring Boot–style configuration loading, but in Python.

`ConfigLoader` is the component that:

* Loads a base configuration (`application.<ext>`)
* Applies a runtime profile overlay (`application-<profile>.<ext>`)
* Expands `${ENV}` variables inside configuration files
* Follows recursive `imports:` statements across multiple files
* Detects circular imports
* Deep-merges structures with clear override semantics
* Wraps encrypted values (`ENC(...)`) with `LazySecret` objects
* Adds internal metadata so applications can introspect how the configuration was built

It is the **heart of SprigConfig**, turning a folder of modular configuration sources into a structured, immutable configuration tree.

---

## 2. Supported Configuration Formats

`ConfigLoader` is **format-agnostic**.

SprigConfig currently supports:

* YAML (`.yml`, `.yaml`)
* JSON (`.json`)
* TOML (`.toml`)

Exactly **one format is active per run**. The active format is determined by the following precedence:

1. An explicit `config_format=` argument passed to `ConfigLoader`
2. The `SPRIGCONFIG_FORMAT` environment variable
3. A default of `yml` if neither is provided

All configuration files involved in a single load (base file, profile overlay, and imports) **must use the active format**. Mixing formats within a single run is intentionally not supported.

**Note on TOML**: When using TOML format, the `imports` directive must be placed at the root level before any table headers (e.g., `[app]`) due to TOML syntax requirements.

---

## 3. Why This File Exists

Python has no native configuration loading standard as powerful as Spring Boot.

Real systems need:

* Profiles (dev, test, prod, etc.)
* Separation between base config and overrides
* Secrets that are not eagerly decrypted
* Modular configuration via file imports
* Strong cycle detection when imports chain together
* A way to trace *exactly how* the final config was constructed
  (e.g., for debugging CI failures or misconfigured deployments)

`ConfigLoader` solves these problems by providing:

### ✔ Predictable ordering

Base → profile overlay → imported files in deterministic merge order.

### ✔ Safety

Circular imports throw explicit `ConfigLoadError`.

### ✔ Transparency

`_meta.sources` and `_meta.import_trace` reveal every file loaded, in order.

### ✔ Secret hygiene

Encrypted values remain encrypted until accessed, preventing accidental logging.

### ✔ Full reproducibility

Given the same directory, profile, and format, the result is always identical.

---

## 4. High-Level Flow of the Loader

### **Step 1: Load `application.<ext>`**

The base configuration file establishes the root config structure.

It is always loaded first and recorded as the **first entry** in the import trace.

---

### **Step 2: Load `application-<profile>.<ext>`**

If a profile overlay exists, it is deeply merged into the base config.

This allows profile-specific overrides, such as:

* Different credentials
* Different host/port values
* Test-specific feature toggles

---

### **Step 3: Apply recursive imports**

Any configuration node may include:

```yaml
imports:
  - imports/common
  - imports/logging
```

**Import Resolution**: Import paths are **extension-less** for portability across formats. The loader automatically appends the active format's extension (`.yml`, `.json`, or `.toml`). This allows the same configuration structure to work across all supported formats without modification.

**Positional Imports**: Imports are **positional** — they merge relative to where the `imports:` key appears in the tree:

* Root-level `imports:` merge at the root
* Nested `imports:` (e.g., `app.imports:`) merge **under that key**
  * If the imported file has `foo: bar`, you get `app.foo: bar`
  * If the imported file has `app: {foo: bar}`, you get `app.app.foo: bar` (nested!)

This positional behavior allows fine-grained control over configuration composition.

**Security**: Import paths are validated to prevent **path traversal attacks**. Imports like `../../etc/passwd` will raise a `ConfigLoadError`. All imports must resolve within the configuration directory.

`ConfigLoader` resolves each import relative to the configuration directory, loads the file using the active format, merges it into the current node, and records the operation.

For each import, the loader tracks:

* Import depth
* Which file imported which
* The order files were processed
* Circular import violations

Imports may appear anywhere in the configuration tree, not just at the root.

---

### **Step 4: Inject the runtime profile**

The loader ensures the active runtime profile is always available under:

```yaml
app:
  profile: <profile>
```

This guarantees the application can introspect the current environment at runtime.

---

### **Step 5: Add internal metadata**

After all merging is complete, the loader injects metadata under:

```yaml
sprigconfig:
  _meta:
    profile: <profile>
    sources: [...]
    import_trace: [...]
```

This metadata supports:

* Debugging configuration merges
* Logging the provenance of runtime settings
* Unit testing and CI verification
* Auditing configuration lineage

---

### **Step 6: Wrap encrypted values**

Any string matching `ENC(...)` is replaced with a `LazySecret` object, for example:

```yaml
db:
  password: ENC(gAAAAABl...)
```

Secrets remain encrypted until explicitly accessed, preventing accidental exposure in logs, dumps, or debug output.

---

## 5. Key Internal Components

### `_load_file(path: Path)`

Reads a configuration file from disk using the active format (YAML, JSON, or TOML), expands environment variables, and returns a Python dictionary. Supports all three formats transparently.

---

### `_resolve_import(import_key: str)`

Resolves an import path by appending the active format's extension if not already present. For example, `imports/common` becomes `imports/common.yml` when using YAML format. Also validates that the resolved path stays within the config directory to prevent path traversal attacks.

---

### `_expand_env(text: str)`

Substitutes `${VAR}` or `${VAR:default}` expressions using environment variables before parsing. Works across all supported formats.

---

### `_apply_imports_recursive(node, ...)`

Walks the entire configuration tree and processes `imports` wherever they appear, maintaining correct import order and cycle detection. Merges imported content **positionally** into the current node where the `imports:` key appears.

---

### `_inject_secrets(data)`

Replaces encrypted values with `LazySecret` wrappers.

---

### `_inject_metadata(merged)`

Populates the `_meta` section with profile, source paths, and detailed import trace information.

---

## 6. Why Import Tracing Matters

Modern deployments depend on:

* CI/CD automation
* Per-environment overlays
* Local developer overrides
* Encrypted secrets

When something behaves unexpectedly, you must be able to answer:

* **Which file set this value?**
* **What order were configs merged in?**
* **Where did this setting originate?**
* **Was something overridden unexpectedly?**

The import trace provides a complete, ordered history of how the final configuration was constructed.

---

## 7. Returned Object: `Config`

The result of `ConfigLoader.load()` is a `Config` object, which:

* Is mapping-like (supports `dict` operations)
* Supports dotted-key lookups (`cfg.get("server.port")`)
* Enforces immutable-ish semantics
* Provides safe `.to_dict()` and `.dump()` behavior
  (secrets are redacted unless explicitly requested)

---

## 8. Summary

`ConfigLoader` provides a **robust, production-grade configuration system** for Python services.

It enables:

* Hierarchical configuration
* Deterministic merges
* Profile-aware overrides
* Secure encrypted secrets
* Full lineage and traceability
* Safety from circular references
* Debuggable, testable configuration behavior

This file is foundational to the SprigConfig project and enables consistent, scalable configuration loading for complex Python applications.
