# Python API Documentation Guide

> **TL;DR:** Standards for writing Python docstrings and API documentation in aiterm

---

## Docstring Style: Google Format

**Use Google-style docstrings** for all public functions, classes, and modules.

**Why Google style:**
- ✅ Readable in code
- ✅ Readable in generated docs
- ✅ Clear section headers
- ✅ Good for ADHD (scannable)

---

## Function Docstrings

### Template

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """Short one-line summary.

    Longer description if needed. Explain what the function does,
    not how it does it.

    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer

    Examples:
        >>> function_name("test", 5)
        True

        >>> function_name("", 0)
        Traceback (most recent call last):
        ValueError: param1 cannot be empty
    """
    pass
```

### Required Sections

**Always include:**
- Short summary (one line)
- `Args` (if function has parameters)
- `Returns` (if function returns value)

**Include when applicable:**
- Longer description (if summary isn't enough)
- `Raises` (if function can raise exceptions)
- `Examples` (for complex functions)
- `Note` (for important details)
- `Warning` (for dangerous operations)

### Examples

**Simple function:**

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b
```

**Function with defaults:**

```python
def greet(name: str, formal: bool = False) -> str:
    """Generate a greeting message.

    Args:
        name: Person's name
        formal: Use formal greeting. Defaults to False.

    Returns:
        Greeting string
    """
    if formal:
        return f"Good day, {name}"
    return f"Hey {name}!"
```

**Function with exceptions:**

```python
def divide(a: float, b: float) -> float:
    """Divide two numbers.

    Args:
        a: Numerator
        b: Denominator

    Returns:
        Result of division

    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
```

**Function with examples:**

```python
def parse_config(path: str) -> dict:
    """Parse configuration file.

    Args:
        path: Path to config file

    Returns:
        Dictionary with configuration

    Examples:
        >>> config = parse_config("config.json")
        >>> config["debug"]
        True
    """
    pass
```

---

## Class Docstrings

### Template

```python
class ClassName:
    """Short one-line summary.

    Longer description of the class purpose.

    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2

    Examples:
        >>> obj = ClassName("value")
        >>> obj.method()
        "result"
    """

    def __init__(self, param: str):
        """Initialize ClassName.

        Args:
            param: Description of param
        """
        self.attr1 = param
        self.attr2 = None

    def method(self) -> str:
        """Short description of method.

        Returns:
            Description of return value
        """
        return "result"
```

### Example: Terminal Backend

```python
class iTerm2Backend:
    """iTerm2 terminal integration.

    Provides methods for controlling iTerm2 via escape sequences
    and Python API integration.

    Attributes:
        profile: Current profile name
        title: Current tab title

    Examples:
        >>> backend = iTerm2Backend()
        >>> backend.switch_profile("R-Dev")
        >>> backend.set_title("R Package Development")
    """

    def __init__(self):
        """Initialize iTerm2 backend."""
        self.profile = None
        self.title = None

    def switch_profile(self, profile: str) -> bool:
        """Switch iTerm2 profile.

        Args:
            profile: Profile name

        Returns:
            True if successful

        Raises:
            TerminalError: If profile doesn't exist
        """
        pass
```

---

## Module Docstrings

**At the top of every module:**

```python
"""Module for MCP server management.

This module provides commands for creating, testing, and managing
MCP servers for Claude Code.

Typical usage:
    from aiterm.mcp import create_server

    create_server("my-server", template="api")
"""
```

---

## Type Hints

**Always use type hints:**

```python
from typing import Optional, List, Dict, Union

def example(
    name: str,
    count: int = 0,
    optional: Optional[str] = None,
    items: List[str] = None
) -> Dict[str, Union[str, int]]:
    """Example with type hints."""
    pass
```

**For complex types:**

```python
from typing import TypedDict, Literal

ProfileType = Literal["R-Dev", "Python-Dev", "Node-Dev"]

class Config(TypedDict):
    """Configuration dictionary."""
    profile: ProfileType
    debug: bool
```

---

## Special Docstring Sections

### Note

```python
def risky_operation():
    """Perform risky operation.

    Note:
        This operation modifies system files. Use with caution.
    """
    pass
```

### Warning

```python
def delete_all():
    """Delete all data.

    Warning:
        This operation cannot be undone!
    """
    pass
```

### Todo

```python
def incomplete_feature():
    """Feature under development.

    Todo:
        - Add error handling
        - Add tests
        - Update documentation
    """
    pass
```

### See Also

```python
def create_server():
    """Create MCP server.

    See Also:
        test_server: For testing created servers
        validate_server: For validating server config
    """
    pass
```

---

## Examples Section

**Use doctest format:**

```python
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b

    Examples:
        >>> multiply(2, 3)
        6

        >>> multiply(0, 100)
        0

        >>> multiply(-1, 5)
        -5
    """
    return a * b
```

**Test examples:**

```bash
python -m doctest src/aiterm/utils.py -v
```

---

## CLI Command Docstrings

**For Typer commands:**

```python
import typer

app = typer.Typer()

@app.command()
def create(
    name: str = typer.Argument(..., help="Server name"),
    template: str = typer.Option("api", help="Template to use")
):
    """Create a new MCP server.

    Creates a new MCP server from a template. The server will be
    created in the current directory.

    Examples:
        aiterm mcp create my-server

        aiterm mcp create my-server --template database
    """
    pass
```

**Shows in help:**

```bash
$ aiterm mcp create --help

Usage: aiterm mcp create [OPTIONS] NAME

  Create a new MCP server.

  Creates a new MCP server from a template. The server will be
  created in the current directory.

  Examples:
      aiterm mcp create my-server

      aiterm mcp create my-server --template database

Arguments:
  NAME  Server name  [required]

Options:
  --template TEXT  Template to use  [default: api]
  --help          Show this message and exit.
```

---

## Documentation Generation

### Using pdoc3

```bash
# Install
pip install pdoc3

# Generate docs
pdoc --html --output-dir docs/api src/aiterm

# Serve docs
pdoc --http :8080 src/aiterm
```

### Integration with MkDocs

```yaml
# mkdocs.yml
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
```

**In markdown:**

```markdown
# API Reference

::: aiterm.mcp.create_server
    options:
      show_source: true
```

---

## Best Practices

### Do's

✅ **Write docstrings for all public functions**
✅ **Include examples for complex functions**
✅ **Use type hints everywhere**
✅ **Keep summaries to one line**
✅ **Describe what, not how**
✅ **Test examples with doctest**

### Don'ts

❌ **Don't write docstrings for obvious functions**
```python
def add(a, b):
    """Add two numbers."""  # Obvious from name
```

❌ **Don't repeat type hints in docstring**
```python
def get_name() -> str:
    """Get name.

    Returns:
        str: The name  # Type already in signature
    """
```

❌ **Don't write implementation details**
```python
def sort_list(items):
    """Sort list.

    Uses quicksort algorithm...  # Implementation detail
    """
```

---

## Quick Reference

| Section | When to Use | Format |
|---------|-------------|--------|
| **Summary** | Always | One line, no period |
| **Description** | Complex functions | Multiple paragraphs |
| **Args** | Has parameters | `param: Description` |
| **Returns** | Returns value | Description of return |
| **Raises** | Can raise | `Error: When...` |
| **Examples** | Complex functions | Doctest format |
| **Note** | Important info | Free text |
| **Warning** | Dangerous ops | Free text |

---

## Checklist

Before committing:

- [ ] All public functions have docstrings
- [ ] All docstrings use Google format
- [ ] Type hints on all functions
- [ ] Examples work (tested with doctest)
- [ ] CLI commands have examples in docstring
- [ ] No implementation details in docstrings

---

**Last Updated:** 2025-12-19
**See Also:** `MKDOCS-GUIDE.md`, [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
