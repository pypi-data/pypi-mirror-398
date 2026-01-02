---
description: Run tests in watch mode
category: testing
---

# Test Watch Mode

Run tests continuously as files change.

## What I'll do

1. Detect test framework (pytest, jest, vitest, etc.)
2. Start tests in watch mode
3. Monitor for file changes
4. Re-run tests automatically

## Supported frameworks

- **Python**: pytest-watch, pytest --watch
- **JavaScript**: jest --watch, vitest --watch, npm run test:watch
- **Go**: go test -watch
- **Rust**: cargo watch -x test

## Usage

Run `/testing:watch` and I'll start the appropriate watch mode!
