# CLI Test Suite for aiterm

Generated: 2025-12-26

## Overview

This directory contains CLI test suites for the `aiterm` command-line tool. Two modes are available:

| Mode | File | Purpose | Use Case |
|------|------|---------|----------|
| **Automated** | `automated-tests.sh` | CI-ready tests | GitHub Actions, pre-commit |
| **Interactive** | `interactive-tests.sh` | Human-guided QA | Manual testing, demos |

## Quick Start

```bash
# Run automated tests (CI mode)
bash tests/cli/automated-tests.sh

# Run with verbose output
VERBOSE=1 bash tests/cli/automated-tests.sh

# Run interactive tests in a new terminal pane
./scripts/run-interactive-tests.sh right    # Split right (recommended)
./scripts/run-interactive-tests.sh below    # Split below
./scripts/run-interactive-tests.sh tab      # New tab
./scripts/run-interactive-tests.sh window   # New window

# Force specific terminal
TERMINAL=iterm2 ./scripts/run-interactive-tests.sh right
TERMINAL=ghostty ./scripts/run-interactive-tests.sh right
```

### Terminal Support

| Terminal | Splits | Tabs | Windows |
|----------|--------|------|---------|
| **Ghostty** (default) | ✅ | ✅ | ✅ |
| **iTerm2** | ✅ | ✅ | ✅ |
| **Terminal.app** | ❌ | ✅ | ✅ |

## Test Coverage

### Smoke Tests (4 tests)
- CLI installation check
- Version command
- Help accessibility
- Alias (aiterm) works

### Core Commands (4 tests)
- `doctor` - System health check
- `detect` - Context detection
- `switch` - Profile switching
- `context detect` - Explicit context

### Claude Subcommands (3 tests)
- `claude settings`
- `claude approvals list`
- `claude --help`

### MCP Subcommands (3 tests)
- `mcp list`
- `mcp validate`
- `mcp --help`

### Sessions Subcommands (4 tests)
- `sessions live`
- `sessions conflicts`
- `sessions history`
- `sessions --help`

### IDE Subcommands (3 tests)
- `ide list`
- `ide compare`
- `ide --help`

### OpenCode Subcommands (2 tests)
- `opencode config`
- `opencode --help`

### Error Handling (2 tests)
- Invalid command handling
- Invalid subcommand handling

### Exit Codes (2 tests)
- Exit 0 on success
- Non-zero on error

### Help Accessibility (7 tests)
- Help for all major subcommand groups

**Total: 34+ test cases**

## Options

### Automated Tests

| Option | Description | Example |
|--------|-------------|---------|
| `VERBOSE=1` | Show detailed output | `VERBOSE=1 ./automated-tests.sh` |
| `BAIL=1` | Stop on first failure | `BAIL=1 ./automated-tests.sh` |

### Interactive Tests

- **y** - Run the test
- **n** - Skip the test
- **s** - Skip the test
- **Ctrl+C** - Abort the session

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All tests passed |
| `1` | One or more tests failed |
| `2` | Test suite error (e.g., CLI not installed) |

## CI Integration

### GitHub Actions

```yaml
- name: Run CLI Tests
  run: |
    bash tests/cli/automated-tests.sh

- name: Run CLI Tests (verbose on failure)
  run: |
    bash tests/cli/automated-tests.sh || VERBOSE=1 bash tests/cli/automated-tests.sh
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run quick CLI smoke tests
BAIL=1 bash tests/cli/automated-tests.sh
```

## Adding New Tests

### Automated Test

Add to `automated-tests.sh`:

```bash
# Test: Description
if ait new-command > /dev/null 2>&1; then
    log_pass "new-command works"
else
    log_fail "new-command failed"
fi
```

### Interactive Test

Add to `interactive-tests.sh`:

```bash
run_test 28 "New Feature" \
    "ait new-command --option" \
    "Expected output description"
```

## Related

- `/craft:test:cli-gen` - Generated this test suite
- `/craft:test:cli-run` - Run test suites
- `pytest tests/` - Python unit tests
- `tests/test_cli.py` - Python CLI tests
