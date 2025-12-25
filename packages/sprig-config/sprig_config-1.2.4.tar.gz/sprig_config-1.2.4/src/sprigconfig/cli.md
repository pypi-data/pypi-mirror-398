# sprigconfig/cli.py — Documentation

This module implements the command-line interface (CLI) for **SprigConfig**, providing a clean, scriptable way to inspect the fully merged configuration produced by `ConfigLoader`.

---

## Overview

The CLI exposes one primary command:

```
sprigconfig dump
```

This command loads configuration from a specified directory, applies profile overlays and imports, resolves secrets (optionally), and outputs the final merged configuration in YAML or JSON.

The CLI is intentionally simple and safe:
- It will refuse to reveal decrypted secrets unless explicitly requested.
- YAML output is always clean and human-readable (no Python object wrappers).
- Errors always produce a non-zero exit code.
- Help output is always available and never depends on application configuration.

---

## Help and Discoverability

The CLI provides first-class, code-defined help behavior:

### Top-level help

```
sprigconfig --help
```

Displays the list of available subcommands with short descriptions. This allows users to discover functionality without trial-and-error.

### Command-specific help

```
sprigconfig dump --help
```

Displays:
- Required and optional arguments
- Clear usage syntax
- Embedded, real-world examples

### Bare command behavior

Running a command without required arguments:

```
sprigconfig dump
```

Will display the command help and examples instead of failing immediately. This avoids argparse’s default “error-first” UX and guides the user toward correct usage.

All help text is defined in code and versioned with the CLI, ensuring it is always available and cannot be broken by missing external files.

---

## Internal Structure

The file is composed of the following pieces:

---

### `_render_pretty_yaml(data)`

Formats Python dictionaries into *clean*, *stable*, and *human-friendly* YAML, with:
- `sort_keys=False` to preserve semantic order
- block-style (`default_flow_style=False`)
- consistent indentation & Unicode handling

This avoids PyYAML's intrusive object tags and ensures round-trip stability.

---

### `_extract_data_for_dump(config, reveal_secrets)`

Converts a SprigConfig `Config` object to a plain dict suitable for serialization.

Key details:

- Calls `Config.to_dict(reveal_secrets=...)`, guaranteeing safe primitive structures.
- Walks the structure recursively:
  - Converts `LazySecret` to either plaintext (`reveal_secrets=True`) or `"ENC(**REDACTED**)"`.
  - Normalizes lists and nested dictionaries.
- Ensures no Python object wrappers (e.g., `!!python/object`) appear in YAML.

This function guarantees that CLI output is production-safe and reusable.

---

### `run_dump(...)`

This is the main execution path for the `dump` command.

Responsibilities:

1. Loads configuration via:
   ```python
   loader = ConfigLoader(config_dir=config_dir, profile=profile)
   config = loader.load()
   ```
2. Captures `ConfigLoadError` and emits a clean message to stderr.
3. Converts config into a clean structure via `_extract_data_for_dump`.
4. Renders the structure as:
   - pretty YAML (`_render_pretty_yaml`)
   - pretty JSON (`json.dumps(..., indent=2)`)
5. Writes to:
   - `stdout`, or
   - an explicitly provided output file (`--output`)

This function is designed for scripting and automated debugging.

---

## The CLI Entry Point (`main()`)

The CLI is built using `argparse` with a subcommand system.

### Subcommand: `dump`

Args:

| Flag | Meaning |
|------|---------|
| `--config-dir PATH` | Required. Directory containing `application.yml` and profiles. |
| `--profile NAME` | Required. Profile to load (e.g., dev, prod, test). |
| `--secrets` | Reveal decrypted secrets (**unsafe**). |
| `--output PATH` | Write output to a file instead of stdout. |
| `--output-format {yaml,json}` | YAML by default; JSON available. |

Example usages printed directly in the help text include:

```
sprigconfig dump --config-dir=config --profile=dev
sprigconfig dump --config-dir=config --profile=prod --secrets
sprigconfig dump --config-dir=config --profile=test --output-format=json
sprigconfig dump --config-dir=config --profile=dev --output out.yml
```

---

## Execution Flow Summary

```
User runs CLI →
 argparse parses args →
  main() dispatches command →
   run_dump() executes →
    ConfigLoader loads config →
     merge/import/profile logic applied →
      Config returned →
   _extract_data_for_dump() normalizes structure →
 Final result pretty-printed as YAML/JSON
```

---

## Why This CLI Exists

SprigConfig’s merging system can be complex:

- base → profile → imported files
- nested imports
- secrets
- metadata tracking (`sprigconfig._meta`)

Developers need a deterministic way to inspect the *final* resolved config tree.
The `dump` CLI provides exactly that:

✔ Debug merging issues  
✔ Verify correct environment expansion  
✔ Confirm profile overlays  
✔ Audit imported file order  
✔ Script config validation in CI pipelines  

It is intentionally simple, safe, and predictable.

---

## Notes for Future Enhancements

- Add `--trace` to print the import graph visually.
- Add `--schema` support for validation before printing.
- Potential integration with `ConfigSingleton` for runtime introspection.

---

Generated documentation for `sprigconfig/cli.py`.
