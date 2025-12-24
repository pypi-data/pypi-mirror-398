# Tripwires
![Tests](https://github.com/mikeAdamss/tripwires/actions/workflows/ci.yml/badge.svg)
![100% Test Coverage](./docs/coverage-100.svg)
![Static Badge](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)

**Deliberately simple file change detection for rapid development cycles.**

Tripwires tracks the effective content of specific files using fast non-cryptographic hashes for change detection, alerting you when they change unexpectedly. It simply asks: "Did this critical file change unexpectedly?"

Works with UTF-8 text files only - binary files are automatically excluded.

**This is about governance, not security.** Any developer with repository access can update both tracked files and the manifest. Tripwires simply adds a deliberate step to catch accidental or unexpected changes during development.

Ideal for catching unintended modifications during AI-assisted coding, refactoring sessions, or dependency updates.

**Preserve your deliberate decisions. Catch the accidents.**

## When to use tripwires

**✅ Useful when:** Rapid iteration cycles, AI-assisted refactoring, protecting sensitive configuration files, team development with frequent changes, or catching accidental modifications during dependency updates.

**⛔ Not useful when:** Defending against malicious actors, working with frequently-changing binary assets, or in environments where the manifest itself isn't trusted or properly reviewed.

## Installation

```bash
pip install tripwires
```

## Simple Workflow

1. 🎯 **Have sensitive files you want to monitor?** → Set tripwires to track them
2. ⚙️ **Set tripwires** → `tripwires init` and add your critical files  
3. ✏️ **File gets changed** → Someone (or something) modifies monitored code
4. 🚨 **Tripwire triggers** → `tripwires check` detects the change and alerts you
5. ✅ **Confirm changes are deliberate** → Review, then `tripwires update` to reset monitoring
6. 🔄 **Fully CI-friendly** → Integrates seamlessly with any CI/CD pipeline

## Commands

Tripwires has just three commands - that's it.

### `tripwires init`

Initialize a new tripwires manifest file.

```bash
tripwires init                                    # Create ./tripwires.yml
tripwires init --path /path/to/project            # Create tripwires.yml in specified directory
tripwires init -p /path/to/project                # Same as above (short form)
tripwires init --manifest custom.yml --force     # Custom name, overwrite if exists
tripwires init -m custom.yml -f                  # Same as above (short form)
```

> **Important:** Always commit your manifest file (e.g., `tripwires.yml`) to source control. The manifest contains the expected hashes that your team and CI/CD pipeline will validate against.

### `tripwires check`

Check all files in the manifest against their expected hashes.

```bash
tripwires check                              # Use ./tripwires.yml
tripwires check --manifest path/to/manifest.yml
tripwires check -m path/to/manifest.yml     # Same as above (short form)
```

**Exit codes:**
- `0` - All files match their expected hashes
- `1` - Hash mismatches detected  
- `2` - Configuration, decoding, or other errors

**Output:** By default, tripwires provides simple CLI-friendly messages with clear visual feedback. The output format can be customized via a simple output interface - see [`docs/OUTPUT.md`](docs/OUTPUT.md) for details.

> **Note for DevOps:** Failed checks return non-zero exit codes, making tripwires compatible with any CI/CD tool that checks command exit status.

### `tripwires update`

Recompute and update all file hashes in the manifest.

```bash
tripwires update                              # Use ./tripwires.yml
tripwires update --manifest path/to/manifest.yml
tripwires update -m path/to/manifest.yml     # Same as above (short form)
```

## CI/CD Integration

Tripwires integrates seamlessly with any CI/CD pipeline. Failed checks return non-zero exit codes, making them compatible with any tool that checks command exit status.

See [`docs/CI_INTEGRATION.md`](docs/CI_INTEGRATION.md) for a GitHub Actions example and setup details.

## Manifest Structure

Tripwires supports flexible manifest structures to organize your tracked files:

```yaml
# Simple flat structure
paths:
  "src/auth.py": "abc123..."
  "config/settings.py": "def456..."

# Or organized groups
groups:
  core-logic:
    description: "Core business logic"
    paths:
      "src/auth.py": "abc123..."
```

See [`docs/MANIFEST.md`](docs/MANIFEST.md) for detailed examples and best practices.

## Features

- **Cross-platform normalization** - Consistent hashes across Linux/macOS/Windows
- **Binary file detection** - Automatically excludes binary files
- **Pathlib integration** - Robust path handling for all platforms
- **Emoji-friendly output** - Clear, visual feedback
- **Extensible output** - Easy to add new output formats

## License

Apache 2.0 License - see LICENSE file for details.
