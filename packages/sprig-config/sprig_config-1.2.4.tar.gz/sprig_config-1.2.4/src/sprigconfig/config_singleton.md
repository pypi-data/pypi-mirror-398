# sprigconfig/config_singleton.py — Explanation and Purpose

This document explains the role of `ConfigSingleton` in SprigConfig, why it exists, what problems it solves, and how application code is expected to interact with it.

---

## 1. What `ConfigSingleton` Is For

SprigConfig’s `ConfigLoader` is powerful but intentionally **not global**.  
Applications typically need one **canonical configuration** loaded at startup and shared everywhere.

In Java/Spring Boot, this is natural—Spring creates a single `ApplicationContext` containing one unified configuration graph.

Python, however, has no built‑in model for:

- Globally‑accessible configuration  
- Enforcing exactly one initialization  
- Preventing accidental reloading  
- Providing a stable config reference across the entire application  

`ConfigSingleton` implements that missing behavior.

It creates **one and only one** global configuration instance for the runtime of the process.

---

## 2. What Problem It Solves

Real apps (APIs, ETL services, schedulers, batch processors) need:

- A single source of truth for external settings  
- Deterministic startup behavior  
- Protection from accidental reinitialization  
- A fast way for any module to fetch the configuration  

Without a singleton, code could easily:

- Load configuration multiple times
- Load with inconsistent directory paths or profiles
- Mutate state unpredictably  
- Cause race conditions in concurrent environments

`ConfigSingleton` ensures **strong guarantees** about configuration lifecycle.

---

## 3. How It Works

### ### Key Behavior

- `initialize(profile, config_dir)`  
  Must be called **exactly once** when the application boots—typically inside a `create_app()` or startup script.

- `get()`  
  Returns the previously loaded `Config` object.  
  If called before initialization, it raises an error to enforce correct startup sequencing.

- `initialize()` is thread‑safe  
  A lock ensures that parallel startup threads cannot race to initialize the config twice.

- Attempts to call `initialize()` more than once always fail  
  This prevents:
  - Accidental reconfiguration  
  - Re-loading from different directories  
  - Tests or background workers from silently resetting config state

- `_clear_all()`  
  This is **strictly for testing**—allowing pytest fixtures to reset the singleton to a blank state before each test.

---

## 4. Class Attributes (Internal Storage)

| Attribute         | Purpose |
|------------------|---------|
| `_instance`      | The global `Config` object returned from `ConfigLoader.load()` |
| `_profile`       | The profile used (dev, prod, test, etc.) |
| `_config_dir`    | Absolute path to the configuration directory |
| `_lock`          | Ensures thread‑safe initialization |

These values remain stable for the entire runtime of the application.

---

## 5. Initialization Flow

### `initialize()`  
1. Validate input arguments  
   - Ensures a real profile string is provided  
   - Ensures `config_dir` resolves to a valid path  

2. Acquire a lock  
   Prevents concurrent initialization.

3. Check whether initialization has already happened  
   - If so → raise `ConfigLoadError`  

4. Create a `ConfigLoader`  
   Pass in `profile` and `config_dir`.

5. Load configuration  
   Result must be a `Config` object.

6. Store configuration in `_instance`  
   Now the entire application can access it.

### `get()`

Simply returns `_instance`.

Throws an error if called before initialization to catch programmer misuse.

---

## 6. Why the Singleton Is Strict

SprigConfig intentionally **does not reload configuration** at runtime.  
Reloading creates:

- Race conditions
- Inconsistent settings halfway through a request or job
- Security concerns (e.g., keys changing mid-process)
- Excessive overhead from repeatedly parsing and merging YAML

A loaded configuration is treated as **immutable** for the lifetime of the process.

This matches:

- Spring Boot semantics  
- Kubernetes/environment-based configuration  
- Production‑grade architecture patterns  

---

## 7. How Applications Should Use It

### Example (FastAPI)

```python
from sprigconfig.config_singleton import ConfigSingleton

def create_app():
    ConfigSingleton.initialize(
        profile=os.getenv("APP_PROFILE", "dev"),
        config_dir="config"
    )

    app = FastAPI()
    return app
```

### Anywhere else in the code:

```python
cfg = ConfigSingleton.get()
db_host = cfg.get("database.host")
```

No module should ever try to reinitialize.

---

## 8. Testing Support

Unit tests often need to:

- Load configuration with different directories
- Use synthetic test profiles
- Reset configuration between test cases

For this reason we expose `_clear_all()`:

```python
ConfigSingleton._clear_all()
```

It wipes the singleton state so the test can start fresh.

This method is **not** for production use.

---

## 9. Summary

`ConfigSingleton` provides a:

- Safe  
- Deterministic  
- Thread‑safe  
- Single‑assignment  

entry point for loading the application's unified configuration.

It ensures:

- No accidental reinitialization  
- No environment drift  
- No inconsistent configs across modules  
- Predictable application startup  

In short, this file enforces **configuration correctness** at the system level and completes SprigConfig’s goal of delivering a Spring‑like configuration experience in Python environments.

---

