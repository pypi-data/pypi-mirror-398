---
description: How to bump the project version
---

# Bump Project Version

This project uses `bump-my-version` to automate version bumping across multiple files.

## Configuration

The configuration is located in `pyproject.toml` under `[tool.bumpversion]`.
It is configured to update:
- `pyproject.toml`
- `src/testio_mcp/__init__.py`
- `src/testio_mcp/api.py`

## Usage

To bump the version, run one of the following commands:

### Patch Bump (0.2.1 -> 0.2.2)
```bash
uv run bump-my-version bump patch
```

### Minor Bump (0.2.1 -> 0.3.0)
```bash
uv run bump-my-version bump minor
```

### Major Bump (0.2.1 -> 1.0.0)
```bash
uv run bump-my-version bump major
```

## What it does

1.  Updates the version string in the configured files.
2.  Creates a git commit with the message "Bump version: {current} → {new}".
3.  Creates a git tag `v{new_version}`.

## Post-Bump (Important)

After bumping the version, you should update `uv.lock` to match the new version:

```bash
uv lock
git add uv.lock
git commit --amend --no-edit
```

## Dry Run

To see what will happen without making changes:

```bash
uv run bump-my-version bump patch --dry-run --verbose
```
