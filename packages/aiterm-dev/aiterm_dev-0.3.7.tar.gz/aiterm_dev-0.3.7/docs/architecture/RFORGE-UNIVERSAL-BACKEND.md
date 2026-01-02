# RForge Universal Backend Strategy (Proposal A)

**Status:** DRAFT
**Date:** 2025-12-27
**Author:** Gemini (DevOps/Arch)
**Goal:** Unified management of `rforge` across Claude, Terminal, and Gemini.

---

## 1. The Core Philosophy: "One Brain, Three Interfaces"

We adopt a **Universal Backend** pattern. The `rforge-mcp` server (TypeScript) is the single source of truth for all R ecosystem logic. We do not duplicate business logic in Python (Gemini) or Bash (Terminal).

### Architecture Diagram

```mermaid
graph TD
    subgraph "The Brain (Source of Truth)"
        MCP[RForge MCP Server]
        Logic[Business Logic (TS)]
        R[R Execution Environment]
        MCP --> Logic
        Logic --> R
    end

    subgraph "Interface 1: Claude"
        CC[Claude Code]
        Config[settings.json]
        CC -- "StdIO" --> MCP
    end

    subgraph "Interface 2: Terminal"
        CLI[rforge CLI]
        Wrapper[Node.js Wrapper]
        CLI -- "StdIO" --> Wrapper
        Wrapper --> MCP
    end

    subgraph "Interface 3: Gemini"
        Gemini[Gemini CLI]
        Bridge[MCP Bridge / Extension]
        Gemini -- "Tool Calls" --> Bridge
        Bridge -- "StdIO" --> MCP
    end
```

---

## 2. Interface Specifications

### A. Claude Code (Native)
*   **Status:** ✅ **Operational**
*   **Mechanism:** Native MCP support via `~/.claude/settings.json`.
*   **Maintenance:** Minimal. Updates to `rforge-mcp` are immediately available to Claude.

### B. Terminal (CLI Wrapper)
*   **Status:** ⚠️ **Basic Prototype**
*   **Current:** Simple wrapper (`node index.js "$@"`) created at `~/.local/bin/rforge`.
*   **Problem:** Output is raw JSON. Hard for humans to read.
*   **Upgrade Plan:**
    1.  **Format Interceptor:** Update the wrapper to detect if output is JSON.
    2.  **Pretty Printing:** Pipe JSON output through `jq` or a lightweight Python formatter (using `rich`) if running in a TTY.
    3.  **Interactive Mode:** Add a `--interactive` flag to prompt for arguments.

### C. Gemini CLI (The Bridge)
*   **Status:** ⏳ **Pending Configuration**
*   **Challenge:** Gemini needs to "see" the MCP tools.
*   **Strategy:**
    1.  **Direct Registration:** If Gemini CLI supports `mcpServers` config, add it there.
    2.  **Extension Bridge:** Use the `mcp-toolbox` extension (referenced in context) to proxy calls to local MCP servers.
    3.  **Function Calling:** Gemini calls `mcp_toolbox.call_tool('rforge', 'tool_name', args)`.

---

## 3. Implementation Roadmap

### Phase 1: The "Rich" CLI (Terminal Experience)
**Goal:** Make the `rforge` command usable for humans, not just machines.

1.  **Create `src/cli-formatter.js` in `rforge-mcp`:**
    *   Parses MCP JSON responses.
    *   Renders Markdown/Tables using a library like `ink` or `chalk`?
    *   *Simpler:* Have the wrapper script pipe to a python one-liner using `rich`.
2.  **Update Wrapper:**
    ```bash
    #!/bin/bash
    # If output is TTY, format it.
    if [ -t 1 ]; then
       node dist/index.js "$@" | python3 -m aiterm.utils.json_formatter
    else
       node dist/index.js "$@"
    fi
    ```

### Phase 2: Gemini "First Class" Citizen
**Goal:** Gemini can plan R packages as effectively as Claude.

1.  **Tool Registration:**
    *   Verify `mcp-toolbox` installation.
    *   Configure `rforge` in `mcp-toolbox` or Gemini's main config.
2.  **Prompt Engineering:**
    *   Add `RFORGE` instructions to `.gemini/GEMINI.md` (similar to how we handled the persona update).
    *   Teach Gemini the `rforge` tool definitions so it knows *when* to call them.

### Phase 3: Unified DevOps
**Goal:** One command to deploy everywhere.

1.  **Build Script (`npm run release`):**
    *   Compiles TypeScript.
    *   Updates `package.json` version.
    *   Publishes to NPM (private or public).
    *   Updates Homebrew formula (for the CLI wrapper).
2.  **Validation:**
    *   Test suite must pass all 3 interfaces:
        *   `test:claude` (Mock MCP client)
        *   `test:cli` (Shell execution)
        *   `test:gemini` (Prompt evaluation)

---

## 4. Immediate Next Steps (Action Items)

1.  [ ] **Dev:** Create the "Rich" formatter for the CLI wrapper.
2.  [ ] **Config:** Verify Gemini can see `rforge` tools (using `mcp-toolbox` or native config).
3.  [ ] **Doc:** Update `aiterm` docs to reflect this "Universal" architecture.

---

**Review Decision:**
- [ ] **Approve:** Proceed with implementation.
- [ ] **Refine:** Modify the terminal wrapper strategy.
- [ ] **Pivot:** Switch to Monorepo approach.
