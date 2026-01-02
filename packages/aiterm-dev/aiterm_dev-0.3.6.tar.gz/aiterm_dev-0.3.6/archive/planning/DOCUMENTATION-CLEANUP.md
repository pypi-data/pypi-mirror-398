# Documentation Cleanup Tasks

**Created:** 2025-12-24
**Status:** Deferred Post-v0.2.0-dev

---

## Overview

The documentation validation system (`aiterm docs`) has identified issues that require systematic cleanup but don't block the v0.2.0-dev release.

---

## ✅ Completed

### Link Validation
- **Status:** 100% clean (9/9 issues fixed)
- **Result:** All internal documentation links validated
- **Commits:**
  - `docs: fix broken documentation links` (7 issues)
  - `docs: fix placeholder link examples in workflow diagram` (2 issues)

---

## 📝 Remaining Tasks

### Code Example Language Tags (29 issues)

**Issue:** Documentation examples marked as `bash` or `python` that are actually:
- Git log output
- Console output examples
- Explanatory diagrams
- Incomplete code snippets (teaching examples)

**Examples:**

1. **AITERM-IMPLEMENTATION-SUMMARY.md:502-504**
   - Current: `python` (fails: 'return' outside function)
   - Should be: `python` with function wrapper OR `text`
   - Reason: Incomplete snippet showing implementation detail

2. **AUTO-UPDATE-TUTORIAL.md:94-97**
   - Current: `bash` (fails: syntax error)
   - Should be: `text` or `console`
   - Reason: Git log output, not executable bash

3. **claude-integration.md:71-75** (and 9 similar)
   - Current: `bash` (fails: syntax errors)
   - Should be: `text`
   - Reason: Showing auto-approval syntax examples, not bash commands

**Pattern:** Most issues are output examples or explanatory content incorrectly tagged as executable code.

**Impact:** Low - doesn't affect functionality, only documentation validation

**Effort:** Medium - requires reviewing 29 examples across 3 files

---

## Recommended Approach

### Option 1: Systematic Language Tag Update (2-3 hours)

**Process:**
1. Review each of the 29 failures
2. Categorize by type:
   - Console output → `text` or `console`
   - Git log → `text`
   - Incomplete snippets → Add function wrapper OR change to `text`
   - Diagrams → `text`
3. Update language tags
4. Re-validate with `aiterm docs test-examples`

**Benefits:**
- Clean validation (0 failures)
- More accurate syntax highlighting
- Better code example organization

**Risks:**
- Time-consuming manual review
- May affect rendering in some markdown viewers

---

### Option 2: Exclude Output Examples from Validation (30 min)

**Process:**
1. Update `DocsValidator.validate_code_examples()` to skip certain patterns:
   ```python
   # Skip examples that are clearly output/explanatory
   skip_patterns = [
       r'#.*commit',  # Git log examples
       r'Bash\(',     # Auto-approval syntax examples
       r'^\+\-.*\│',  # Table/diagram examples
   ]
   ```
2. Add `--strict` flag for full validation when needed

**Benefits:**
- Quick fix
- Maintains validation for actual code
- Flexible for different use cases

**Risks:**
- May miss real issues in skipped examples
- Adds complexity to validator

---

### Option 3: Defer (Current Choice)

**Rationale:**
- v0.2.0-dev is feature-complete
- Link validation is 100% clean (critical)
- Code examples don't affect functionality
- Can address in v0.2.1 or v0.3.0

**Benefits:**
- Ship v0.2.0-dev on schedule
- User testing reveals actual priorities
- Can batch with other doc improvements

---

## Files Affected

| File | Issues | Type |
|------|--------|------|
| AITERM-IMPLEMENTATION-SUMMARY.md | 1 | Incomplete snippet |
| AUTO-UPDATE-TUTORIAL.md | 3 | Git log output |
| guide/claude-integration.md | 10 | Auto-approval examples |
| AUTO-UPDATE-WORKFLOW.md | 4 | Diagram/output |
| MCP-INTEGRATION.md | 3 | Console output |
| DOCS-HELPERS.md | 8 | Console output |

---

## Validation Commands

```bash
# Check current status
aiterm docs test-examples

# View specific file issues
aiterm docs test-examples --language bash
aiterm docs test-examples --language python

# After fixes, validate all
aiterm docs validate-all
```

---

## Decision Log

**2025-12-24:** Deferred to post-v0.2.0-dev
- **Reason:** Link validation complete, code examples are documentation-only
- **Impact:** Low - doesn't block release
- **Timeline:** Address in v0.2.1 or v0.3.0 based on user feedback

---

## See Also

- `docs/DOCS-HELPERS.md` - Documentation validation guide
- `PHASE-3A-COMPLETE.md` - Phase 3A summary
- `RELEASE-NOTES-v0.2.0-dev.md` - v0.2.0-dev release notes
