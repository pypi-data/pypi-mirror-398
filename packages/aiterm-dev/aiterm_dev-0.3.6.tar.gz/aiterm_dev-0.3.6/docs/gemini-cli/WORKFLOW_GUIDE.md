# Developer Workflow Guide: iterm2-context-switcher

This guide outlines the standard development workflow for the `iterm2-context-switcher` project, leveraging the Gemini CLI, Jules, and integrated tools.

## 1. 🌅 Daily Start
*Initialize your environment and sync with the team.*

*   **Step 1: Context Detection**
    *   **Command:** `ait detect`
    *   **Why:** Verifies you are in the correct iTerm2 profile (e.g., "Dev-Tools" or "Python-Dev") and environment.
*   **Step 2: Sync & Check Issues**
    *   **Command (Gemini):** "Search for open issues assigned to me in this repo."
    *   **Action:** `git pull` (via shell or agent) to get latest changes.

## 2. 💻 Development Loop
*The core cycle: Plan -> Code -> Verify.*

### A. Feature Development (Interactive)
*For focused, single-file changes.*

1.  **Plan:** "I need to add a status bar component for API quota."
2.  **Act:**
    *   **Command (Gemini):** "Create `src/aiterm/status/quota.py` with a class `QuotaDisplay`. Use the `ContextInfo` dataclass."
3.  **Refine:** "Add a method to fetch usage from the env var `AITERM_QUOTA`."
4.  **Verify:** "Create a test for this in `tests/test_quota.py` and run it."

### B. Complex Refactoring (Agentic)
*For cross-cutting changes or "boring" maintenance.*

1.  **Trigger Jules:**
    *   **Command:** `/jules start "Refactor the detection logic in src/aiterm/context/ to use a Strategy pattern instead of if/elif blocks."`
2.  **Monitor:** Check status via `/jules status` or the console link.
3.  **Review:** Once Jules finishes, review the PR/changes using `/code-review`.

### C. Visual Assets (Documentation)
*Generating icons or diagrams for features.*

1.  **Generate Icon:**
    *   **Command:** `/icon prompt="Status bar gauge icon" style=flat sizes=[64]`
2.  **Generate Diagram:**
    *   **Command:** `/diagram prompt="Flowchart of the context detection logic: Path -> Git Check -> File Probes -> ContextType" type=flowchart`

## 3. 🧪 Testing & Quality
*Ensure code stability before committing.*

*   **Run Tests:**
    *   **Command (Gemini):** "Run all tests." (Executes `pytest`)
    *   **Targeted:** "Run tests for the `detector` module only."
*   **Linting:**
    *   **Command (Shell):** `ruff check .`
*   **Code Review:**
    *   **Command:** `/code-review` (Get an AI critique of your unstaged changes).

## 4. 🚀 Release & Documentation
*Ship changes and update docs.*

1.  **Update Changelog:**
    *   **Command (Gemini):** "Read `CHANGELOG.md` and add a new entry for [Feature Name] under Unreleased."
2.  **Commit:**
    *   **Command (Gemini):** "Generate a conventional commit message for these changes."
3.  **Push:**
    *   **Command (Shell):** `git push`

## 5. 🛠 Essential Command Reference

| Context | Tool | Command | Example / Usage |
| :--- | :--- | :--- | :--- |
| **Project** | `aiterm` | `ait detect` | Show current detected context |
| | | `ait doctor` | diagnostic check |
| **Agent** | `jules` | `/jules start <task>` | Start async refactoring task |
| | | `/jules status` | Check task progress |
| **Docs** | `nano` | `/diagram ...` | Generate architecture diagrams |
| **Quality** | `review` | `/code-review` | AI review of local changes |
| **Search** | `mcp` | "Search issues..." | Find GitHub issues via natural language |

## 6. measurable Outcomes
*   **Velocity:** Reduce context-switching time by utilizing `ait detect`.
*   **Quality:** 100% test pass rate required before `/code-review`.
*   **Consistency:** All visual assets generated via `/icon` or `/diagram` for uniform style.
