# Documentation Helpers

**Status:** ✅ Complete (v0.2.0-dev)

The documentation helpers provide tools to validate and maintain high-quality documentation for the aiterm project.

## Overview

Documentation quality is critical for open-source projects. The `aiterm docs` commands help you:

- 🔗 **Validate Links** - Find broken internal and external links
- 💻 **Test Code Examples** - Verify code examples are syntactically valid
- 📊 **Track Statistics** - Monitor documentation health metrics
- ✅ **Comprehensive Validation** - Run all checks at once

**Key Features:**
- Fast validation of markdown files
- Broken link detection (internal + external)
- Missing anchor detection
- Code example syntax checking (Python, Bash)
- Beautiful Rich output with actionable errors
- Integration with CI/CD pipelines

---

## Quick Start

```bash
# Show documentation statistics
aiterm docs stats

# Validate all links (internal only - fast)
aiterm docs validate-links

# Test code examples
aiterm docs test-examples

# Run all validation checks
aiterm docs validate-all

# Check external URLs (slow but comprehensive)
aiterm docs validate-links --external
```

---

## Commands

### `aiterm docs stats`

Show statistics about your documentation.

**Output:**
```
📊 Documentation Statistics
┌────────────────┬────────┐
│ Total files    │     27 │
│ Total lines    │ 14,381 │
│ Total links    │    204 │
│ Total examples │    533 │
└────────────────┴────────┘

   Code Examples by   
       Language       
┏━━━━━━━━━━━━┳━━━━━━━┓
┃ Language   ┃ Count ┃
┡━━━━━━━━━━━━╇━━━━━━━┩
│ bash       │   311 │
│ python     │    74 │
│ json       │    13 │
└────────────┴───────┘
```

**Options:**
- `--docs-dir, -d` - Specify documentation directory (default: `./docs`)

**Use Cases:**
- Track documentation growth over time
- See which languages dominate examples
- Get quick overview of docs size

---

### `aiterm docs validate-links`

Validate all markdown links in documentation.

**What It Checks:**
- ✅ Internal links point to existing files
- ✅ Anchor references exist in target files  
- ✅ Links don't point outside docs directory
- ✅ External URLs are reachable (with `--external`)

**Options:**
- `--docs-dir, -d` - Specify documentation directory (default: `./docs`)
- `--external, -e` - Check external URLs (slow, uses curl)

**Example Output (Success):**
```bash
aiterm docs validate-links
```
```
Validating documentation links...

✓ All links are valid!
```

**Example Output (Issues Found):**
```
Validating documentation links...

                🔗 Link Validation Results (6 issues)                
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ File                   ┃ Line ┃ Type     ┃ Issue               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ docs/API.md            │  270 │ Anchor   │ Anchor not found:   │
│                        │      │          │ #context-object     │
│ docs/INTEGRATION.md    │  590 │ Internal │ Link points outside │
│                        │      │          │ docs directory      │
└────────────────────────┴──────┴──────────┴─────────────────────┘
```

**Link Types:**
- **Internal**: Relative links within docs directory
- **Anchor**: Hash links to headings (`#section-name`)
- **External**: HTTP/HTTPS URLs (only with `--external`)

**Use Cases:**
- Pre-commit validation
- CI/CD pipeline checks
- Regular documentation maintenance
- Finding broken cross-references

**Performance:**
- Internal link checking: ~1 second for 200+ links
- External link checking: ~10-30 seconds (network dependent)

---

### `aiterm docs test-examples`

Test code examples for syntax errors.

**What It Checks:**
- ✅ Python code compiles without syntax errors
- ✅ Bash scripts have valid syntax
- ✅ Code blocks are properly formatted

**Options:**
- `--docs-dir, -d` - Specify documentation directory (default: `./docs`)
- `--language, -l` - Test only specific language (`python` or `bash`)

**Example Output (Success):**
```bash
aiterm docs test-examples
```
```
Testing code examples...

✓ All 385 code example(s) are valid!
```

**Example Output (Failures):**
```
Testing code examples...

            💻 Code Example Validation (3 failures)            
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ File            ┃ Lines   ┃ Language ┃ Error           ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ docs/API.md     │ 502-504 │ python   │ 'return'        │
│                 │         │          │ outside         │
│                 │         │          │ function        │
│ docs/GUIDE.md   │ 94-97   │ bash     │ syntax error    │
│                 │         │          │ near token `('  │
└─────────────────┴─────────┴──────────┴─────────────────┘

✗ 3/385 example(s) failed validation
```

**Validation Methods:**
- **Python**: Uses `compile()` to check syntax
- **Bash**: Uses `bash -n` for syntax checking

**Use Cases:**
- Ensure examples are copy-pasteable
- Catch typos in code blocks
- Verify documentation stays in sync with code
- Pre-publish validation

**Limitations:**
- Does not execute code (only syntax checking)
- Cannot validate runtime errors
- Some examples may be intentionally incomplete snippets

---

### `aiterm docs validate-all`

Run all documentation validation checks at once.

**What It Checks:**
- ✅ All internal links
- ✅ All code examples (Python + Bash)
- ✅ Optional: External URLs (with `--external`)

**Options:**
- `--docs-dir, -d` - Specify documentation directory (default: `./docs`)
- `--external, -e` - Include external URL checking (slow)

**Example Output:**
```bash
aiterm docs validate-all
```
```
Running all documentation checks...

     📚 Documentation     
    Validation Summary    
┌──────────────────┬─────┐
│ Files scanned    │ 27  │
│ Links checked    │ 204 │
│ Code examples    │ 533 │
│ Link issues      │ 0 ✓ │
│ Example failures │ 0 ✓ │
└──────────────────┴─────┘

✓ Documentation validation passed! ✨
```

**Example Output (Issues Found):**
```
Running all documentation checks...

     📚 Documentation     
    Validation Summary    
┌──────────────────┬─────┐
│ Files scanned    │ 27  │
│ Links checked    │ 204 │
│ Code examples    │ 533 │
│ Link issues      │ 6   │
│ Example failures │ 29  │
└──────────────────┴─────┘

✗ Found 35 issue(s) in documentation

Run specific commands for details:
  aiterm docs validate-links
  aiterm docs test-examples
```

**Use Cases:**
- Pre-release validation
- CI/CD pipeline checks
- Regular documentation health checks
- One-command quality gate

**Exit Codes:**
- `0` - All checks passed
- `1` - Issues found (suitable for CI/CD)

---

## Configuration

### Documentation Directory

By default, all commands look for documentation in `./docs`.

**Override:**
```bash
# Use different directory
aiterm docs stats --docs-dir ./documentation

# Use absolute path
aiterm docs validate-all --docs-dir /path/to/docs
```

### External Link Checking

External link checking is **disabled by default** because:
- Slow (network requests for each URL)
- May have false positives (rate limiting, temporary outages)
- Not always necessary for internal docs

**Enable:**
```bash
# Check external URLs
aiterm docs validate-links --external

# Include in comprehensive validation
aiterm docs validate-all --external
```

---

## Common Workflows

### 1. Pre-Commit Documentation Check

Run before committing documentation changes:

```bash
# Quick validation (internal links + examples)
aiterm docs validate-all

# If clean, commit
git add docs/
git commit -m "docs: update API reference"
```

### 2. CI/CD Pipeline Integration

Add to `.github/workflows/docs.yml`:

```yaml
name: Documentation Quality

on: [push, pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install aiterm
        run: pip install -e .
      
      - name: Validate documentation
        run: aiterm docs validate-all
```

### 3. Regular Documentation Audit

Monthly documentation health check:

```bash
# Get current stats
aiterm docs stats > docs-stats-$(date +%Y-%m).txt

# Check all links including external
aiterm docs validate-all --external > docs-validation-$(date +%Y-%m).txt

# Review and fix issues
less docs-validation-*.txt
```

### 4. Documentation Release Checklist

Before releasing new documentation:

```bash
# 1. Check statistics
aiterm docs stats

# 2. Validate links (including external)
aiterm docs validate-links --external

# 3. Test code examples
aiterm docs test-examples

# 4. Comprehensive validation
aiterm docs validate-all --external
```

---

## Troubleshooting

### False Positives in Link Checking

**Issue:** Valid links reported as broken

**Common Causes:**
1. **Relative path resolution**: Link works in GitHub but not locally
2. **Case sensitivity**: `File.md` vs `file.md` on case-sensitive filesystems
3. **Trailing slashes**: `docs/guide/` vs `docs/guide`

**Solutions:**
- Use explicit `.md` extensions in links
- Match case exactly
- Prefer `file.md` over `file/` for directories

### Code Examples Failing Validation

**Issue:** Intentionally incomplete examples fail

**Common Causes:**
1. **Placeholder code**: `...` or `# implementation here`
2. **Partial snippets**: Only showing relevant lines
3. **Output examples**: Not meant to be executed

**Solutions:**

**Option 1: Use `text` language:**
````markdown
```text
from module import something
...
```
````

**Option 2: Make example valid:**
````markdown
```python
from module import something

def example():
    pass  # implementation here
```
````

**Option 3: Skip validation:**
Only test specific languages:
```bash
aiterm docs test-examples --language python
```

### External Link Timeouts

**Issue:** External link validation is very slow

**Solutions:**
1. **Skip external links for local testing:**
   ```bash
   aiterm docs validate-links  # No --external flag
   ```

2. **Run external checks less frequently:**
   - Local: Skip external links
   - CI: Include external links in nightly builds only

3. **Ignore problematic domains:**
   - Some sites block automated requests
   - Focus on links you control

---

## Architecture

### DocsValidator Class

**Location:** `src/aiterm/docs/validator.py`

**Key Methods:**

#### `validate_links(check_external=False)`

Scans all markdown files for links and validates them.

**Returns:** `List[LinkIssue]`

**Process:**
1. Find all markdown files in docs directory
2. Extract links using regex pattern
3. Build set of valid internal files
4. Extract headings to build anchor map
5. Validate each link:
   - Internal: Check file exists, anchor exists
   - External: Optional HTTP HEAD request

#### `extract_code_examples()`

Extract all fenced code blocks from documentation.

**Returns:** `List[CodeExample]`

**Process:**
1. Scan markdown files line by line
2. Detect code fence starts (` ``` `)
3. Extract language identifier
4. Capture code content
5. Record file, line numbers, language

#### `validate_code_examples(languages=None)`

Validate code examples by checking syntax.

**Returns:** `List[Dict[str, Any]]`

**Process:**
1. Extract all code examples
2. Filter by requested languages
3. For Python: Use `compile()` to check syntax
4. For Bash: Use `bash -n` to check syntax
5. Collect failures with line numbers and errors

#### `validate_all(check_external_links=False)`

Run comprehensive validation.

**Returns:** `ValidationResult`

**Process:**
1. Validate all links
2. Extract and validate code examples
3. Compile statistics
4. Return results object

### ValidationResult Dataclass

**Fields:**
- `total_files: int` - Number of markdown files scanned
- `total_links: int` - Total links found
- `total_examples: int` - Total code examples found
- `link_issues: List[LinkIssue]` - Broken links
- `example_failures: List[Dict]` - Invalid code examples
- `warnings: List[str]` - Non-critical warnings

**Properties:**
- `has_issues: bool` - True if any issues found
- `issue_count: int` - Total number of issues

---

## Integration

### Python API

**Import:**
```python
from aiterm.docs import DocsValidator
```

**Example: Validate Links**
```python
from aiterm.docs import DocsValidator
from pathlib import Path

validator = DocsValidator(docs_dir=Path("docs"))
issues = validator.validate_links()

for issue in issues:
    print(f"{issue.file}:{issue.line} - {issue.message}")
```

**Example: Extract Code Examples**
```python
validator = DocsValidator()
examples = validator.extract_code_examples()

python_examples = [e for e in examples if e.language == "python"]
print(f"Found {len(python_examples)} Python examples")

for example in python_examples:
    print(f"{example.file}:{example.line_start}-{example.line_end}")
    print(example.code[:100])  # First 100 chars
```

**Example: Comprehensive Validation**
```python
validator = DocsValidator()
result = validator.validate_all(check_external_links=True)

print(f"Scanned {result.total_files} files")
print(f"Found {result.issue_count} issues")

if result.has_issues:
    print("\nLink Issues:")
    for issue in result.link_issues:
        print(f"  - {issue.file}:{issue.line}: {issue.message}")
    
    print("\nCode Failures:")
    for failure in result.example_failures:
        print(f"  - {failure['file']}: {failure['error']}")
```

---

## Examples

### Example 1: Find All Broken Links

```python
from aiterm.docs import DocsValidator

validator = DocsValidator()
issues = validator.validate_links()

broken_internal = [i for i in issues if i.issue_type == "broken_internal"]
missing_anchors = [i for i in issues if i.issue_type == "missing_anchor"]

print(f"Broken internal links: {len(broken_internal)}")
print(f"Missing anchors: {len(missing_anchors)}")
```

### Example 2: Extract Python Examples to Test File

```python
from aiterm.docs import DocsValidator

validator = DocsValidator()
examples = validator.extract_code_examples()

python_examples = [e for e in examples if e.language.lower() == "python"]

# Write to test file
with open("test_doc_examples.py", "w") as f:
    for i, example in enumerate(python_examples):
        f.write(f"# Example {i+1} from {example.file}\n")
        f.write(f"# Lines {example.line_start}-{example.line_end}\n")
        f.write(example.code)
        f.write("\n\n")
```

### Example 3: Documentation Quality Report

```python
from aiterm.docs import DocsValidator

validator = DocsValidator()
result = validator.validate_all()

print("Documentation Quality Report")
print("=" * 50)
print(f"Files scanned: {result.total_files}")
print(f"Links: {result.total_links}")
print(f"Code examples: {result.total_examples}")
print()
print(f"Issues found: {result.issue_count}")
print(f"  - Broken links: {len(result.link_issues)}")
print(f"  - Invalid examples: {len(result.example_failures)}")
print()

if result.has_issues:
    print("FAILED - Documentation has issues")
else:
    print("PASSED - Documentation is clean!")
```

---

## See Also

- [aiterm API Reference](api/AITERM-API.md)
- [aiterm User Guide](guides/AITERM-USER-GUIDE.md)
- [MCP Integration Guide](MCP-INTEGRATION.md)

---

**Version:** v0.2.0-dev  
**Last Updated:** 2025-12-24  
**Status:** ✅ Complete
