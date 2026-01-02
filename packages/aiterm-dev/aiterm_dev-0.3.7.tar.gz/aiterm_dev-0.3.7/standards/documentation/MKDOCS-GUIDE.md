# MkDocs Documentation Guide

> **TL;DR:** Guidelines for writing MkDocs documentation for aiterm

---

## MkDocs Structure

### Standard Layout

```
docs/
├── index.md                    # Homepage
├── getting-started/
│   ├── installation.md
│   └── quickstart.md
├── tutorials/
│   ├── getting-started/
│   │   └── 01-installation.md
│   └── mcp-creation/
│       └── 01-your-first-server.md
├── ref-cards/
│   ├── aiterm-commands.md
│   └── mcp-server-api.md
├── examples/
│   └── servers/
│       └── simple-api/
└── reference/
    ├── configuration.md
    └── troubleshooting.md
```

### Navigation (mkdocs.yml)

```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
  - Tutorials:
    - Getting Started:
      - Installation: tutorials/getting-started/01-installation.md
    - MCP Creation:
      - Your First Server: tutorials/mcp-creation/01-your-first-server.md
  - Reference Cards:
    - aiterm Commands: ref-cards/aiterm-commands.md
    - MCP Server API: ref-cards/mcp-server-api.md
  - Reference:
    - Configuration: reference/configuration.md
    - Troubleshooting: reference/troubleshooting.md
```

---

## Writing Guidelines

### Page Structure

Every page should have:

1. **Title** (H1) - Single title at top
2. **TL;DR** (blockquote) - One sentence summary
3. **Sections** (H2) - Clear logical sections
4. **Examples** (code blocks) - Runnable examples

**Template:**

```markdown
# Page Title

> **TL;DR:** One sentence describing what this page covers.

## Section 1

Content here...

\`\`\`bash
# Example command
command --option
\`\`\`

## Section 2

...
```

### Code Blocks

**Always specify language:**

```markdown
\`\`\`python
def example():
    pass
\`\`\`

\`\`\`bash
aiterm --help
\`\`\`

\`\`\`yaml
key: value
\`\`\`
```

**Add titles for clarity:**

```markdown
\`\`\`python title="src/aiterm/cli/main.py"
def main():
    pass
\`\`\`
```

**Highlight lines:**

```markdown
\`\`\`python hl_lines="2 3"
def example():
    important_line = 1  # This is highlighted
    another_one = 2     # This too
    normal_line = 3
\`\`\`
```

### Admonitions

Use admonitions for callouts:

```markdown
!!! note
    This is a note with useful information.

!!! tip
    Pro tip for advanced users.

!!! warning
    Be careful with this operation.

!!! danger
    This can break things if misused.

!!! example
    Here's how to do it...
```

**Collapsible admonitions:**

```markdown
??? note "Click to expand"
    Hidden content here.

???+ tip "Expanded by default"
    This starts open.
```

### Tables

**Always use tables for comparisons:**

```markdown
| Feature | aiterm | Alternative |
|---------|--------|-------------|
| Speed   | Fast   | Slow        |
| ADHD    | Yes    | No          |
```

**Align columns:**

```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| L    | C      | R     |
```

### Links

**Internal links:**

```markdown
See [Installation](getting-started/installation.md) for setup.

Jump to [specific section](page.md#section-name).
```

**External links:**

```markdown
Check out [Claude Code](https://code.claude.com).
```

**Reference-style links (for repeated URLs):**

```markdown
See [docs][claude-docs] and [API][claude-api].

[claude-docs]: https://code.claude.com/docs
[claude-api]: https://code.claude.com/api
```

---

## Material Theme Features

### Tabs

```markdown
=== "Tab 1"
    Content for tab 1

=== "Tab 2"
    Content for tab 2
```

### Task Lists

```markdown
- [x] Completed task
- [ ] Pending task
- [ ] Another pending task
```

### Emoji

```markdown
:rocket: Launch
:check: Done
:warning: Warning
:bulb: Tip
```

### Annotations

```markdown
Some text with a note. (1)
{ .annotate }

1. This is the annotation content.
```

---

## Best Practices

### ADHD-Friendly

1. **TL;DR at top** - One sentence summary
2. **Visual hierarchy** - Clear headings (H2, H3)
3. **Code examples** - Show, don't just tell
4. **Lists over paragraphs** - Scannable content
5. **Tables for comparisons** - Easy to compare options

### Navigation

1. **Max 3 levels deep** - Home → Category → Page
2. **Logical grouping** - Related pages together
3. **Short titles** - "Installation" not "How to Install"
4. **Breadcrumbs enabled** - In theme config

### Content

1. **One concept per page** - Don't cram too much
2. **Progressive disclosure** - Basic → Advanced
3. **Copy-paste ready** - All commands runnable
4. **Expected output** - Show what success looks like

---

## Examples

### Good Documentation Page

```markdown
# Creating Your First MCP Server

> **TL;DR:** Create a working MCP server in 10 minutes using aiterm templates.

## Prerequisites

- aiterm installed
- Basic Python knowledge
- 10 minutes

## Step 1: Choose a Template

\`\`\`bash
aiterm mcp templates
\`\`\`

**Output:**
\`\`\`
Available templates:
1. simple-api    - REST API server
2. database      - Database integration
3. custom        - Blank template
\`\`\`

## Step 2: Create Server

\`\`\`bash
aiterm mcp create my-server --template simple-api
\`\`\`

!!! tip
    Use `simple-api` for your first server.

## Step 3: Test It

\`\`\`bash
aiterm mcp test my-server
\`\`\`

## What You Built

- [x] Working MCP server
- [x] Basic API integration
- [x] Ready to customize

## Next Steps

- [Advanced Configuration](02-configuration.md)
- [Adding Tools](03-adding-tools.md)
```

### Bad Documentation Page

```markdown
# MCP Servers

MCP servers are really cool. They let you do things.
You can create them with aiterm.

There are different types of MCP servers. Some are for APIs.
Some are for databases. You choose what you want.

To create one, run a command. Then test it. Then use it.

...
```

**Why bad:**
- ❌ No TL;DR
- ❌ Vague content
- ❌ No examples
- ❌ No structure
- ❌ No actionable steps

---

## Markdown Extensions

### Enabled in aiterm

From `mkdocs.yml`:

```yaml
markdown_extensions:
  - pymdownx.highlight       # Syntax highlighting
  - pymdownx.inlinehilite    # Inline code highlighting
  - pymdownx.snippets        # Include external files
  - pymdownx.superfences     # Nested code blocks, tabs
  - pymdownx.tabbed         # Content tabs
  - pymdownx.tasklist       # Task lists with checkboxes
  - admonition              # Callout boxes
  - pymdownx.details        # Collapsible admonitions
  - attr_list               # Add HTML attributes
  - tables                  # GFM tables
  - pymdownx.emoji          # Emoji support
```

### Usage Examples

**Superfences (nested blocks):**

````markdown
\`\`\`python
def outer():
    \`\`\`python
    # Nested code
    \`\`\`
\`\`\`
````

**Tabbed content:**

```markdown
=== "Python"
    \`\`\`python
    print("Hello")
    \`\`\`

=== "Bash"
    \`\`\`bash
    echo "Hello"
    \`\`\`
```

**Task lists:**

```markdown
- [x] Setup complete
- [ ] Documentation needed
```

---

## Quick Checklist

Before publishing a page:

- [ ] TL;DR at top
- [ ] Code examples work (tested)
- [ ] All commands copy-paste ready
- [ ] Headings use H2/H3 (not H4+)
- [ ] Tables for comparisons
- [ ] Admonitions for important notes
- [ ] Links all work
- [ ] Navigation updated in `mkdocs.yml`

---

**Last Updated:** 2025-12-19
**See Also:** `../adhd/TUTORIAL-TEMPLATE.md`, `../adhd/REFCARD-TEMPLATE.md`
