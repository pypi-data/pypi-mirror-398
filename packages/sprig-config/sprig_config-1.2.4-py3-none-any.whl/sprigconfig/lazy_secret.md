# sprigconfig/lazy_secret.py — Explanation and Purpose

This document explains the design, purpose, and behavior of the `LazySecret` subsystem in SprigConfig, including global key management and secure secret handling.

---

## 1. What `LazySecret` Is For

Modern applications must store secrets (DB passwords, API tokens, encryption keys) inside configuration files — but they *must not* allow these secrets to appear in logs, stack traces, or debug dumps.

SprigConfig solves this by:

- Allowing encrypted values inside YAML (`ENC(...)`)
- Deferring decryption until absolutely necessary (“lazy” decryption)
- Avoiding storing raw secrets in config objects
- Providing strict, secure key resolution rules
- Supporting dynamic key providers (rotation, vault-based loading)

`LazySecret` is therefore the security engine of SprigConfig’s configuration system.

---

## 2. Why This File Exists

Typical config loaders eagerly parse all values. That is dangerous for secrets:

- A stack trace might log the decrypted value.
- A `.dump()` operation could accidentally leak credentials.
- Multiple components might store secrets in unprotected strings.
- Developers may accidentally print configs and leak sensitive data.

SprigConfig’s philosophy:

### **Secrets should not be decrypted unless explicitly requested.**

This file provides:

- The `LazySecret` class  
- Global key management  
- Optional dynamic key provider logic  
- Validation and safe key resolution  
- Backward compatibility for legacy calling code  

---

## 3. Encrypted Config Format

A secret in YAML looks like:

```yaml
db:
  password: ENC(gAAAAABlZx...)
```

`ConfigLoader` wraps that in a `LazySecret` instance instead of decrypting it.

The ciphertext is stored safely until the application explicitly calls `.get()`.

---

## 4. Global Key Management API

### ### `_GLOBAL_KEY`
Stores a single Fernet key used for decrypting all secrets (unless an explicit key is passed).

### `set_global_key(key: str)`
Sets and validates the key immediately.

- Ensures the key is non-empty  
- Ensures the key is a valid base64 Fernet key  
- Prevents invalid cryptographic material from entering the system  

### `get_global_key()`
For diagnostics only — never for normal application use.

### `set_key_provider(provider)`
Allows registering a function that returns a Fernet key dynamically.

Examples:

- Rotating keys
- Fetching from Vault
- Loading from secure hardware storage

### `ensure_key_from_env()`
Utility for lazy initialization based on:

```
APP_SECRET_KEY=<base64key>
```

Useful when applications want SprigConfig to initialize itself before loading configs.

---

## 5. Key Resolution Rules

The function `_resolve_key()` determines which key to use when decrypting a secret.

Priority order:

1. **Explicit key** passed to the `LazySecret` constructor  
2. **Global key** previously set  
3. **Dynamic key provider**, if registered  
4. **Environment variable** `APP_SECRET_KEY`

If none of these provide a usable key, a `ConfigLoadError` is raised.

### Recursion guard
If a key provider indirectly triggers more key resolution, the system detects it and throws an error to prevent infinite loops.

---

## 6. How `LazySecret` Works

The `LazySecret` class wraps encrypted values and decrypts them only when accessed.

### Constructor

```python
LazySecret("ENC(gAAAAA...)")
```

It:

- Strips the `ENC(...)` wrapper
- Stores ciphertext only
- Does *not* decrypt yet

### `.get()`

Returns the decrypted secret value.

### `__str__()`

Also decrypts — but applications should be careful when coercing secrets to strings.

### `.zeroize()`

Attempts to overwrite decrypted material in memory:

```python
mysecret.zeroize()
```

While Python cannot fully guarantee secure memory handling, this is the best-effort equivalent of clearing sensitive buffers.

---

## 7. Why Lazy Decryption Matters

### **Security benefits**

- Secrets do not appear in config dumps  
- Logging the config won’t leak passwords  
- Developers cannot accidentally inspect decrypted values  
- Secrets remain encrypted in memory until use  
- Works cleanly with pytest or debugging tools  

### **Operational benefits**

- Supports key rotation  
- Allows secure runtime environments (e.g., Kubernetes) to inject keys only at startup  
- Ensures consistent behavior across imports, overlays, and deep merges  

---

## 8. Backward Compatibility

Older versions of SprigConfig exposed a symbol named `_key_provider`.  
To maintain compatibility:

```python
if "_key_provider" not in globals():
    def _key_provider():
        return os.getenv("APP_SECRET_KEY")
```

This prevents breaking existing codebases that still reference the legacy name.

---

## 9. Summary

`lazy_secret.py` provides:

- Secure, lazy secret decryption
- Strong global key handling
- Strict validation and error reporting
- Optional dynamic key resolution
- Compatibility with older integrations

It is one of the foundational security components of SprigConfig and ensures that configuration-driven applications can handle secrets safely and predictably.

---

