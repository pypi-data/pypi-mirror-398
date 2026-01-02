# CLI Test Enhancement Plan

**Created:** 2025-12-26
**Status:** In Progress
**Priority:** High (for CI integration)

---

## Overview

Enhancements to the CLI test suites (`tests/cli/automated-tests.sh` and `tests/cli/interactive-tests.sh`) to improve reliability, CI integration, and developer experience.

---

## Enhancement Priorities

### 🔴 High Priority (Complete)

#### 1. JUnit XML Output for CI
**Status:** ✅ Complete (Dec 26, 2025)
**Benefit:** GitHub Actions test summary integration

```bash
# Usage
bash tests/cli/automated-tests.sh --junit results.xml
```

Features:
- Machine-readable test results
- GitHub Actions annotation support
- Test duration tracking
- Failure message capture

#### 2. Performance Benchmarking
**Status:** ✅ Complete (Dec 26, 2025)
**Benefit:** Catch performance regressions early

```bash
# Benchmark specific commands
benchmark_test "Version (fast)" "ait --version" 500  # max 500ms
benchmark_test "Doctor" "ait doctor" 5000            # max 5s
```

Features:
- Command execution timing
- Configurable max duration per test
- Warning when exceeding threshold
- Performance summary in output

---

### 🟡 Medium Priority (Future)

#### 3. Snapshot Testing
**Effort:** 2 hours
**Benefit:** Output validation, regression detection

```bash
# First run creates snapshots
SNAPSHOT_DIR="tests/cli/snapshots"

# Subsequent runs diff against snapshots
test_with_snapshot "Version" "ait --version"
```

#### 4. Test Tags for Selective Runs
**Effort:** 1 hour
**Benefit:** Faster CI for PRs

```bash
# Run only smoke tests
RUN_TAGS=smoke bash tests/cli/automated-tests.sh

# Run slow integration tests
RUN_TAGS=integration bash tests/cli/automated-tests.sh
```

#### 5. Command Coverage Tracking
**Effort:** 1 hour
**Benefit:** Ensure no commands forgotten

```bash
# Auto-discover commands from --help
# Track which are tested
# Report coverage percentage
```

---

### 🟢 Low Priority (Backlog)

#### 6. Parallel Test Execution
**Effort:** 2 hours
**Benefit:** 3-5x faster on multi-core

#### 7. Environment Isolation
**Effort:** 1 hour
**Benefit:** Reproducible tests

#### 8. Cross-Platform Support
**Effort:** 3 hours
**Benefit:** Linux CI runners

#### 9. Retry Logic for Flaky Tests
**Effort:** 30 min
**Benefit:** Reduce false failures

#### 10. Interactive Test Improvements
**Effort:** 1 hour
**Benefit:** Better UX for long sessions
- Rerun option (r)
- Skip option (s)
- Progress save/resume

---

## Implementation Details

### JUnit XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="aiterm-cli" tests="34" failures="0" time="12.5">
    <testcase name="Version Check" time="0.045"/>
    <testcase name="Help Output" time="0.052"/>
    <testcase name="Invalid Command" time="0.038">
      <failure message="Expected error message not found"/>
    </testcase>
  </testsuite>
</testsuites>
```

### Performance Benchmark Output

```
━━━ Performance Benchmarks ━━━
✅ PASS: Version (45ms, max: 500ms)
✅ PASS: Help (52ms, max: 500ms)
✅ PASS: Doctor (1234ms, max: 5000ms)
⚠️  SLOW: MCP Test All (8521ms, max: 5000ms)

Performance Summary:
  Fast (< 500ms): 28 tests
  Medium (< 2s):   4 tests
  Slow (> 2s):     2 tests
```

---

## CI Integration

### GitHub Actions Workflow

```yaml
- name: Run CLI Tests
  run: |
    bash tests/cli/automated-tests.sh --junit test-results.xml

- name: Upload Test Results
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: test-results
    path: test-results.xml

- name: Publish Test Results
  uses: EnricoMi/publish-unit-test-result-action@v2
  if: always()
  with:
    files: test-results.xml
```

---

## Files Modified

- `tests/cli/automated-tests.sh` - JUnit output, benchmarks
- `tests/cli/interactive-tests.sh` - Enhanced prompts (future)
- `.github/workflows/test.yml` - JUnit upload
- `CLI-TEST-ENHANCEMENTS.md` - This document

---

## Success Metrics

- [x] JUnit XML generates valid output
- [x] GitHub Actions shows test summary (CI workflow updated)
- [x] Performance benchmarks catch slow commands
- [x] No regressions in existing tests (34/34 pass)
