# Pytest Configuration Error - Fix Summary

## Issue Resolved ✅

**Problem**: pytest failed with error about unrecognized arguments (`--cov`, `--timeout`)

**Root Cause**: System was using global pytest installation (`/Users/masa/.local/bin/pytest`) which lacked required plugins, instead of the project's `.venv` pytest which has all plugins installed.

## Solution

### Immediate Fix

```bash
# Activate the project virtual environment
cd /Users/masa/Projects/mcp-ticketer
source .venv/bin/activate

# Verify pytest works
pytest --version
```

### Why This Works

The `.venv` directory contains a complete Python environment with all required pytest plugins:

```
pytest                 8.4.2
pytest-asyncio        1.2.0
pytest-cov            7.0.0    ✅ Provides --cov option
pytest-mock           3.15.1
pytest-timeout        2.4.0    ✅ Provides --timeout option
pytest-xdist          3.6.1
```

These plugins are required by the `pytest.ini` configuration but were missing from the global pytest installation.

## Environment Details

### Project Virtual Environments

| Directory | Status | Plugins Installed |
|-----------|--------|-------------------|
| `.venv/` | ✅ **Active & Complete** | All dev dependencies |
| `venv/` | ⚠️ Exists but outdated | Not recommended |

### Pytest Locations

| Path | Has Plugins | Recommendation |
|------|-------------|----------------|
| `/Users/masa/.local/bin/pytest` | ❌ No | Don't use |
| `.venv/bin/pytest` | ✅ Yes | **Use this** |

## Verification Steps

After activating `.venv`, verify the setup:

```bash
# 1. Check pytest location
which pytest
# Expected: /Users/masa/Projects/mcp-ticketer/.venv/bin/pytest

# 2. Check pytest version
pytest --version
# Expected: pytest 8.4.2 (no errors)

# 3. Check installed plugins
pip list | grep pytest
# Expected: All pytest-* packages listed

# 4. Test pytest can collect tests
pytest --co -q tests/ | head -10
# Expected: List of test files without errors
```

## Required pytest.ini Configuration

The `pytest.ini` file requires these plugins:

```ini
[pytest]
addopts =
    --cov=src/mcp_ticketer          # Requires: pytest-cov>=4.1.0
    --cov-branch
    --cov-report=term-missing:skip-covered
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=12
    --timeout=60                     # Requires: pytest-timeout>=2.2.0
    --timeout-method=thread
```

## Development Workflow

### Daily Development

```bash
# Start of every development session:
cd /Users/masa/Projects/mcp-ticketer
source .venv/bin/activate

# Now all commands work correctly:
pytest                    # Run tests
make test                 # Run tests via Makefile
make test-parallel        # Parallel testing (3-4x faster)
make quality              # Code quality checks
```

### Running Tests

```bash
# After activating .venv:
pytest                           # All tests
pytest tests/test_file.py        # Specific file
pytest -k "test_name"            # Specific test pattern
pytest -v                        # Verbose output
make test-parallel               # Fastest (parallel execution)
```

## Common Mistakes

### ❌ Don't Do This

```bash
# Running pytest without activating venv
pytest  # Uses wrong pytest with missing plugins
```

### ✅ Do This Instead

```bash
# Always activate venv first
source .venv/bin/activate
pytest  # Uses correct pytest with all plugins
```

## IDE Configuration

### VS Code

Create/update `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestPath": "${workspaceFolder}/.venv/bin/pytest"
}
```

### PyCharm

1. Settings → Project → Python Interpreter
2. Add → Existing environment
3. Select: `/Users/masa/Projects/mcp-ticketer/.venv/bin/python`

## Documentation References

- **Full Guide**: [docs/DEVELOPMENT_ENVIRONMENT.md](DEVELOPMENT_ENVIRONMENT.md)
- **Build System**: [docs/DEVELOPMENT.md](DEVELOPMENT.md)
- **Makefile Reference**: [.makefiles/QUICK_REFERENCE.md](../.makefiles/QUICK_REFERENCE.md)

## Testing the Fix

```bash
# Full verification sequence
cd /Users/masa/Projects/mcp-ticketer
source .venv/bin/activate

# Should all succeed without errors:
pytest --version
pytest --co -q tests/ | head -5
make test-parallel
```

## Key Takeaway

**Always activate `.venv` before running any development commands.**

This ensures you're using the correct Python environment with all required dependencies and plugins installed.

---

**Date Fixed**: 2025-11-24
**Python Version**: 3.13.7
**Pytest Version**: 8.4.2
**Status**: ✅ Resolved
