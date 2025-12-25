# sprigconfig/help.py — Help Metadata Documentation

This module defines **code-based CLI help metadata** for SprigConfig.

It exists to centralize human-facing help text (summaries and examples) in a
single, version-controlled location, while keeping the CLI bootstrap logic
simple, robust, and free of external file dependencies.

---

## Purpose

`help.py` provides structured metadata used by the CLI to:

- Populate top-level command listings (e.g. `sprigconfig --help`)
- Provide short command summaries
- Display real-world usage examples
- Improve discoverability without argparse boilerplate
- Ensure help output is always available, even in broken environments

This design deliberately avoids external `help.yml` files to prevent
bootstrap fragility and filesystem dependency issues.

---

## Design Principles

The help system follows these rules:

- **Code-defined truth**  
  Help metadata is versioned with the code and cannot go missing.

- **Zero runtime dependencies**  
  No configuration loading, no profiles, no imports, no secrets.

- **Declarative, not procedural**  
  This module contains data only — no logic.

- **CLI-scoped**  
  Help metadata belongs to the CLI layer, not application configuration.

---

## Structure

The module exposes a single public constant:

```python
COMMAND_HELP
```

This is a dictionary keyed by subcommand name.

### Schema

```text
COMMAND_HELP
  └── <command>
       ├── summary   (str)   — short, one-line description
       └── examples  (list)  — realistic CLI usage examples
```

---

## Current Commands

### `dump`

```python
COMMAND_HELP = {
    "dump": {
        "summary": "Dump merged configuration for inspection/debugging",
        "examples": [
            "sprigconfig dump --config-dir=config --profile=dev",
            "sprigconfig dump --config-dir=config --profile=prod --secrets",
            "sprigconfig dump --config-dir=config --profile=test --output-format=json",
            "sprigconfig dump --config-dir=config --profile=dev --output out.yml",
        ],
    }
}
```

#### Summary

> Dump merged configuration for inspection/debugging

#### Examples

```
sprigconfig dump --config-dir=config --profile=dev
sprigconfig dump --config-dir=config --profile=prod --secrets
sprigconfig dump --config-dir=config --profile=test --output-format=json
sprigconfig dump --config-dir=config --profile=dev --output out.yml
```

These examples are displayed directly in CLI help output and are intended to be:

- Copy/paste ready
- Representative of real-world usage
- Safe by default (with explicit opt-in for secrets)

---

## How the CLI Uses This Module

The CLI imports `COMMAND_HELP` at startup and uses it to:

- Populate `argparse` subparser summaries
- Render examples in command-specific help
- Display a friendly command list when no arguments are provided

Because this metadata is pure Python data, it is:

- Always available
- Cheap to import
- Safe during early CLI bootstrap

---

## Extending Help Metadata

When adding a new CLI command:

1. Add a new entry to `COMMAND_HELP`
2. Provide:
   - A concise summary
   - At least one realistic example
3. Wire the command into `cli.py`

No additional files or configuration changes are required.

---

## Why This File Exists (Even Though It’s Small)

Although `help.py` is intentionally minimal, it serves an important role:

- Prevents help text duplication
- Keeps CLI logic readable
- Establishes a clear pattern for future commands
- Enables future doc generation if needed

This file trades a few lines of data for long-term clarity and robustness.

---

Generated documentation for `sprigconfig/help.py`.
