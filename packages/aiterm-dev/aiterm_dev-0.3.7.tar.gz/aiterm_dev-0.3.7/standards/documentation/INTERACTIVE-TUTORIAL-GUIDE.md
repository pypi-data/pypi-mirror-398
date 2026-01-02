# Interactive Tutorial Guide

> **TL;DR:** Guidelines for creating web-based interactive tutorials for aiterm

---

## Purpose

Interactive tutorials allow users to:
- Learn by doing (code in browser)
- See results immediately (live preview)
- Download generated code
- Try different options

**Use for:** MCP server creation, plugin development, hook configuration

---

## Structure

### Directory Layout

```
docs/interactive/
├── mcp-creator/
│   ├── index.html          # Main page
│   ├── style.css           # Styling
│   ├── app.js              # Interactive logic
│   ├── templates/          # Code templates
│   │   ├── simple-api.js
│   │   └── database.js
│   └── examples/           # Example outputs
│       └── sample-server.zip
├── hook-builder/
│   └── ...
└── plugin-wizard/
    └── ...
```

### Page Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>MCP Server Creator</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Header -->
    <header>
        <h1>Create Your MCP Server</h1>
        <p>Interactive MCP server builder</p>
    </header>

    <!-- Configuration Form -->
    <section class="config">
        <h2>1. Configure</h2>
        <!-- Input fields -->
    </section>

    <!-- Live Preview -->
    <section class="preview">
        <h2>2. Preview</h2>
        <pre><code id="code-preview"></code></pre>
    </section>

    <!-- Download -->
    <section class="download">
        <h2>3. Download</h2>
        <button id="download-btn">Download Server</button>
    </section>

    <script src="app.js"></script>
</body>
</html>
```

---

## Components

### 1. Configuration Form

**Progressive disclosure - show options step-by-step:**

```html
<form id="config-form">
    <!-- Step 1: Basic Info -->
    <div class="step active" data-step="1">
        <h3>Step 1: Basic Information</h3>
        <label for="server-name">Server Name:</label>
        <input type="text" id="server-name" placeholder="my-server">

        <label for="description">Description:</label>
        <input type="text" id="description" placeholder="My MCP server">

        <button class="next-btn">Next →</button>
    </div>

    <!-- Step 2: Template -->
    <div class="step" data-step="2">
        <h3>Step 2: Choose Template</h3>
        <div class="template-grid">
            <div class="template-card" data-template="api">
                <h4>REST API</h4>
                <p>Connect to REST APIs</p>
            </div>
            <div class="template-card" data-template="database">
                <h4>Database</h4>
                <p>Query databases</p>
            </div>
        </div>

        <button class="prev-btn">← Back</button>
        <button class="next-btn">Next →</button>
    </div>

    <!-- Step 3: Customize -->
    <div class="step" data-step="3">
        <h3>Step 3: Add Tools</h3>
        <!-- Tool configuration -->

        <button class="prev-btn">← Back</button>
        <button class="generate-btn">Generate →</button>
    </div>
</form>
```

### 2. Live Code Preview

**Update preview as user types:**

```html
<div class="preview-container">
    <div class="preview-tabs">
        <button class="tab active" data-file="index.js">index.js</button>
        <button class="tab" data-file="package.json">package.json</button>
        <button class="tab" data-file="README.md">README.md</button>
    </div>

    <div class="preview-content">
        <pre><code class="language-javascript" id="preview"></code></pre>
    </div>

    <div class="preview-actions">
        <button id="copy-btn">📋 Copy</button>
        <button id="download-btn">⬇️ Download</button>
    </div>
</div>
```

### 3. File Download

**Generate ZIP with all files:**

```javascript
// Using JSZip library
async function downloadServer() {
    const zip = new JSZip();

    // Add files
    zip.file("index.js", generateIndexJS());
    zip.file("package.json", generatePackageJSON());
    zip.file("README.md", generateREADME());

    // Create tools directory
    const tools = zip.folder("tools");
    tools.file("example.js", generateExampleTool());

    // Generate and download
    const content = await zip.generateAsync({type: "blob"});
    saveAs(content, `${serverName}.zip`);
}
```

---

## JavaScript Logic

### Template System

```javascript
// templates/simple-api.js
const templates = {
    'simple-api': {
        name: 'REST API Server',
        description: 'Connect to REST APIs',

        generate(config) {
            return `
import { Server } from '@modelcontextprotocol/sdk/server/index.js';

const server = new Server({
    name: "${config.name}",
    version: "1.0.0"
});

server.setRequestHandler("tools/list", async () => {
    return {
        tools: [
            {
                name: "fetch_api",
                description: "${config.description}",
                inputSchema: {
                    type: "object",
                    properties: {
                        endpoint: {
                            type: "string",
                            description: "API endpoint"
                        }
                    }
                }
            }
        ]
    };
});

export { server };
            `.trim();
        }
    }
};
```

### Reactive Updates

```javascript
// Update preview when config changes
document.querySelectorAll('input, select, textarea').forEach(input => {
    input.addEventListener('input', () => {
        updatePreview();
    });
});

function updatePreview() {
    const config = getConfig();
    const template = templates[config.template];
    const code = template.generate(config);

    document.getElementById('preview').textContent = code;

    // Syntax highlighting (if using Prism.js)
    Prism.highlightElement(document.getElementById('preview'));
}
```

### Step Navigation

```javascript
let currentStep = 1;

document.querySelectorAll('.next-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        if (validateStep(currentStep)) {
            currentStep++;
            showStep(currentStep);
        }
    });
});

document.querySelectorAll('.prev-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        currentStep--;
        showStep(currentStep);
    });
});

function showStep(step) {
    document.querySelectorAll('.step').forEach((el, index) => {
        el.classList.toggle('active', index + 1 === step);
    });
}

function validateStep(step) {
    // Validate current step before proceeding
    const stepEl = document.querySelector(`.step[data-step="${step}"]`);
    const inputs = stepEl.querySelectorAll('input[required]');

    for (const input of inputs) {
        if (!input.value) {
            input.classList.add('error');
            return false;
        }
    }

    return true;
}
```

---

## Styling

### Layout

```css
/* Container */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Two-column layout */
.layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
}

@media (max-width: 768px) {
    .layout {
        grid-template-columns: 1fr;
    }
}
```

### Steps

```css
/* Step indicator */
.steps {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
}

.step-indicator {
    width: 3rem;
    height: 3rem;
    border-radius: 50%;
    background: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.step-indicator.active {
    background: #007bff;
    color: white;
}

.step-indicator.completed {
    background: #28a745;
    color: white;
}
```

### Preview

```css
/* Code preview */
.preview-container {
    background: #1e1e1e;
    border-radius: 8px;
    overflow: hidden;
}

.preview-tabs {
    display: flex;
    background: #2d2d2d;
    border-bottom: 1px solid #444;
}

.tab {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
}

.tab.active {
    color: white;
    background: #1e1e1e;
}

.preview-content {
    padding: 1rem;
    max-height: 500px;
    overflow-y: auto;
}

.preview-content code {
    color: #d4d4d4;
    font-family: 'Fira Code', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
}
```

---

## Libraries

### Recommended

```html
<!-- JSZip for file downloads -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

<!-- FileSaver for downloads -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"></script>

<!-- Prism for syntax highlighting -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>

<!-- Optional: Monaco Editor for advanced editing -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs/loader.min.js"></script>
```

---

## Best Practices

### ADHD-Friendly

✅ **One step at a time** - Don't show all options at once
✅ **Instant feedback** - Update preview immediately
✅ **Visual progress** - Show step indicator
✅ **Clear actions** - "Next", "Back", "Generate" buttons
✅ **Example values** - Pre-fill with placeholders

### Performance

✅ **Debounce updates** - Don't update on every keystroke
✅ **Lazy load templates** - Load only when selected
✅ **Minify code** - Use build tools for production

### Accessibility

✅ **Keyboard navigation** - Tab through steps
✅ **ARIA labels** - Screen reader support
✅ **Focus indicators** - Show what's focused
✅ **Error messages** - Clear validation feedback

---

## Example: MCP Creator

**File:** `docs/interactive/mcp-creator/index.html`

**Features:**
- Step-by-step server creation
- 10+ templates to choose from
- Live code preview
- Download as ZIP
- Copy individual files
- Test server online (future)

**Workflow:**
1. Enter server name
2. Choose template
3. Configure tools
4. Customize options
5. Preview generated code
6. Download ZIP

---

## Hosting

### GitHub Pages

```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Interactive Tutorials

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/interactive
```

**URL:** `https://data-wise.github.io/aiterm/interactive/mcp-creator/`

---

## Testing

### Manual Testing

- [ ] All steps navigate correctly
- [ ] Preview updates on input
- [ ] Download generates valid ZIP
- [ ] Code is syntactically correct
- [ ] Works on mobile
- [ ] Works in all browsers

### Automated Testing

```javascript
// Using Jest + Puppeteer
describe('MCP Creator', () => {
    test('generates valid server code', async () => {
        await page.goto('http://localhost:8000/interactive/mcp-creator/');

        await page.type('#server-name', 'test-server');
        await page.click('[data-template="api"]');
        await page.click('.generate-btn');

        const code = await page.textContent('#preview');
        expect(code).toContain('const server = new Server');
    });
});
```

---

## Checklist

Before publishing:

- [ ] All templates work
- [ ] Download generates valid files
- [ ] Preview syntax highlights correctly
- [ ] Step validation works
- [ ] Mobile-responsive
- [ ] Accessible (keyboard nav, ARIA)
- [ ] Fast (<1s preview update)
- [ ] Error messages clear

---

**Last Updated:** 2025-12-19
**See Also:** `MKDOCS-GUIDE.md`, [MCP Server Examples](https://modelcontextprotocol.io/examples)
