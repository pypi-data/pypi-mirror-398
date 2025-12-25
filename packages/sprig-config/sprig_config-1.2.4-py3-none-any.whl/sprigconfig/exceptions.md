# exceptions.md

## ConfigLoadError

**Location:** `sprigconfig/exceptions.py`

### Purpose
`ConfigLoadError` is the unified exception type raised whenever SprigConfig is unable to load, parse, merge, or otherwise process configuration files.

It intentionally wraps all configuration‑related failures so higher‑level components (e.g., the CLI, FastAPI apps, ETL services) can safely catch a single error type rather than handling multiple low‑level exceptions.

### When It Is Raised
Typical scenarios include:

- Missing `application.yml` or invalid YAML syntax  
- Unresolvable environment variable expansions  
- Circular imports detected during config processing  
- Failure to decrypt secrets when `reveal_secrets=True`  
- Attempting to use `ConfigSingleton` incorrectly (e.g., calling `get()` before `initialize()`)  
- Failure to write a YAML dump to disk  

### Example Usage

```python
from sprigconfig import load_config, ConfigLoadError

try:
    cfg = load_config(profile="dev", config_dir="/etc/app")
except ConfigLoadError as e:
    print(f"Failed to load configuration: {e}")
```

### Design Intent

- **Keeps error handling consistent** across the entire SprigConfig ecosystem.  
- Ensures **clean user-facing error messages** in CLI utilities.  
- Allows developers to catch a *single* exception rather than chasing several possible internal failures.

