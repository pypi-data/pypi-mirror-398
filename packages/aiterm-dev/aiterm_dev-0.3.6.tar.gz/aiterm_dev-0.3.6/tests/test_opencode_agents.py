#!/usr/bin/env python3
"""
OpenCode Agents & Configuration Test Suite
===========================================
Validates OpenCode Phase 2 configuration including:
- Custom agents (r-dev, quick)
- GitHub MCP integration
- CLAUDE.md instruction sync
- Environment setup

Run with: python tests/test_opencode_agents.py
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TestResult:
    name: str
    passed: bool
    details: str
    category: str = "general"


def log(msg: str, level: str = "INFO") -> None:
    """Print with timestamp and level."""
    ts = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
    print(f"[{ts}] {symbols.get(level, '•')} {msg}")


class OpenCodeAgentTester:
    """Test suite for OpenCode agent configuration."""

    def __init__(self):
        self.config_path = Path.home() / ".config/opencode/config.json"
        self.agents_md = Path.home() / ".config/opencode/AGENTS.md"
        self.claude_md = Path.home() / ".claude/CLAUDE.md"
        self.results: list[TestResult] = []
        self.config = None

    def load_config(self) -> bool:
        """Load OpenCode configuration."""
        if not self.config_path.exists():
            return False
        try:
            self.config = json.loads(self.config_path.read_text())
            return True
        except json.JSONDecodeError:
            return False

    # ─── Config Tests ────────────────────────────────────────────────────────

    def test_config_exists(self) -> TestResult:
        """Test 1: Config file exists and is valid JSON."""
        if not self.config_path.exists():
            return TestResult("Config Exists", False, f"Not found: {self.config_path}", "config")

        if not self.load_config():
            return TestResult("Config Exists", False, "Invalid JSON", "config")

        return TestResult("Config Exists", True, f"Found: {self.config_path}", "config")

    def test_model_configured(self) -> TestResult:
        """Test 2: Primary model is explicitly set."""
        if not self.config:
            return TestResult("Model Configured", False, "No config loaded", "config")

        model = self.config.get("model", "")
        if not model:
            return TestResult("Model Configured", False, "No model specified", "config")

        expected = "anthropic/claude-sonnet-4-5"
        if model == expected:
            return TestResult("Model Configured", True, f"Model: {model}", "config")
        else:
            return TestResult("Model Configured", True, f"Model: {model} (expected {expected})", "config")

    def test_small_model_configured(self) -> TestResult:
        """Test 3: Small model is explicitly set."""
        if not self.config:
            return TestResult("Small Model", False, "No config loaded", "config")

        model = self.config.get("small_model", "")
        if not model:
            return TestResult("Small Model", False, "No small_model specified", "config")

        return TestResult("Small Model", True, f"Small model: {model}", "config")

    # ─── Agent Tests ─────────────────────────────────────────────────────────

    def test_rdev_agent_exists(self) -> TestResult:
        """Test 4: r-dev agent is configured."""
        if not self.config:
            return TestResult("r-dev Agent", False, "No config loaded", "agents")

        agents = self.config.get("agents", {})
        if "r-dev" not in agents:
            return TestResult("r-dev Agent", False, "Agent not found", "agents")

        agent = agents["r-dev"]
        desc = agent.get("description", "no description")
        model = agent.get("model", "default")
        tools = agent.get("tools", [])

        return TestResult(
            "r-dev Agent",
            True,
            f"Model: {model}, Tools: {len(tools)}, Desc: {desc[:30]}...",
            "agents"
        )

    def test_quick_agent_exists(self) -> TestResult:
        """Test 5: quick agent is configured."""
        if not self.config:
            return TestResult("quick Agent", False, "No config loaded", "agents")

        agents = self.config.get("agents", {})
        if "quick" not in agents:
            return TestResult("quick Agent", False, "Agent not found", "agents")

        agent = agents["quick"]
        model = agent.get("model", "default")
        tools = agent.get("tools", [])

        # Verify it uses Haiku (fast model)
        is_fast = "haiku" in model.lower()

        return TestResult(
            "quick Agent",
            True,
            f"Model: {model} ({'fast ✓' if is_fast else 'not haiku'}), Tools: {len(tools)}",
            "agents"
        )

    def test_agent_tools_valid(self) -> TestResult:
        """Test 6: Agent tools are valid tool names."""
        if not self.config:
            return TestResult("Agent Tools", False, "No config loaded", "agents")

        valid_tools = {"bash", "read", "write", "edit", "glob", "grep", "task", "websearch", "webfetch"}
        agents = self.config.get("agents", {})

        issues = []
        for name, agent in agents.items():
            tools = set(agent.get("tools", []))
            invalid = tools - valid_tools
            if invalid:
                issues.append(f"{name}: {invalid}")

        if issues:
            return TestResult("Agent Tools", False, f"Invalid tools: {issues}", "agents")

        return TestResult("Agent Tools", True, "All agent tools are valid", "agents")

    # ─── MCP Tests ───────────────────────────────────────────────────────────

    def test_github_mcp_enabled(self) -> TestResult:
        """Test 7: GitHub MCP server is enabled."""
        if not self.config:
            return TestResult("GitHub MCP", False, "No config loaded", "mcp")

        mcp = self.config.get("mcp", {})
        github = mcp.get("github", {})

        if not github:
            return TestResult("GitHub MCP", False, "GitHub server not configured", "mcp")

        enabled = github.get("enabled", False)
        if not enabled:
            return TestResult("GitHub MCP", False, "GitHub server disabled", "mcp")

        return TestResult("GitHub MCP", True, "GitHub MCP enabled", "mcp")

    def test_essential_mcp_enabled(self) -> TestResult:
        """Test 8: Essential MCP servers (filesystem, memory) are enabled."""
        if not self.config:
            return TestResult("Essential MCPs", False, "No config loaded", "mcp")

        mcp = self.config.get("mcp", {})
        essential = ["filesystem", "memory"]

        missing = []
        disabled = []
        for server in essential:
            if server not in mcp:
                missing.append(server)
            elif not mcp[server].get("enabled", False):
                disabled.append(server)

        if missing:
            return TestResult("Essential MCPs", False, f"Missing: {missing}", "mcp")
        if disabled:
            return TestResult("Essential MCPs", False, f"Disabled: {disabled}", "mcp")

        return TestResult("Essential MCPs", True, "filesystem + memory enabled", "mcp")

    def test_heavy_mcp_disabled(self) -> TestResult:
        """Test 9: Heavy MCP servers are disabled for performance."""
        if not self.config:
            return TestResult("Heavy MCPs", False, "No config loaded", "mcp")

        mcp = self.config.get("mcp", {})
        heavy = ["sequential-thinking", "playwright", "puppeteer"]

        enabled_heavy = []
        for server in heavy:
            if server in mcp and mcp[server].get("enabled", False):
                enabled_heavy.append(server)

        if enabled_heavy:
            return TestResult("Heavy MCPs", False, f"Still enabled: {enabled_heavy}", "mcp")

        return TestResult("Heavy MCPs", True, "Heavy servers disabled (good for perf)", "mcp")

    # ─── Instructions Tests ──────────────────────────────────────────────────

    def test_instructions_configured(self) -> TestResult:
        """Test 10: Instructions array includes CLAUDE.md."""
        if not self.config:
            return TestResult("Instructions Config", False, "No config loaded", "sync")

        instructions = self.config.get("instructions", [])
        if not instructions:
            return TestResult("Instructions Config", False, "No instructions configured", "sync")

        has_claude = any("CLAUDE.md" in str(i) for i in instructions)
        has_rules = any(".claude/rules" in str(i) for i in instructions)

        if not has_claude:
            return TestResult("Instructions Config", False, "CLAUDE.md not in instructions", "sync")

        details = f"Found: {instructions}"
        if has_rules:
            details += " (includes rules/*.md)"

        return TestResult("Instructions Config", True, details, "sync")

    def test_agents_md_symlink(self) -> TestResult:
        """Test 11: AGENTS.md is symlinked to CLAUDE.md."""
        if not self.agents_md.exists():
            return TestResult("AGENTS.md Symlink", False, "AGENTS.md not found", "sync")

        if not self.agents_md.is_symlink():
            return TestResult("AGENTS.md Symlink", False, "AGENTS.md is not a symlink", "sync")

        target = self.agents_md.resolve()
        if target == self.claude_md.resolve():
            return TestResult("AGENTS.md Symlink", True, f"→ {target}", "sync")
        else:
            return TestResult("AGENTS.md Symlink", False, f"Points to {target}, not CLAUDE.md", "sync")

    def test_claude_md_exists(self) -> TestResult:
        """Test 12: Global CLAUDE.md exists."""
        if not self.claude_md.exists():
            return TestResult("CLAUDE.md Exists", False, f"Not found: {self.claude_md}", "sync")

        size = self.claude_md.stat().st_size
        return TestResult("CLAUDE.md Exists", True, f"Found ({size} bytes)", "sync")

    # ─── Environment Tests ───────────────────────────────────────────────────

    def test_github_token_available(self) -> TestResult:
        """Test 13: GITHUB_TOKEN can be obtained from gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
                masked = f"{token[:4]}...{token[-4:]}"
                return TestResult("GITHUB_TOKEN", True, f"Available via gh CLI: {masked}", "env")
            else:
                return TestResult("GITHUB_TOKEN", False, "gh auth token failed", "env")
        except FileNotFoundError:
            return TestResult("GITHUB_TOKEN", False, "gh CLI not installed", "env")
        except subprocess.TimeoutExpired:
            return TestResult("GITHUB_TOKEN", False, "Timeout getting token", "env")

    def test_opencode_installed(self) -> TestResult:
        """Test 14: OpenCode CLI is installed."""
        try:
            result = subprocess.run(
                ["opencode", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return TestResult("OpenCode Installed", True, f"Version: {version}", "env")
            else:
                return TestResult("OpenCode Installed", False, "Command failed", "env")
        except FileNotFoundError:
            return TestResult("OpenCode Installed", False, "opencode not in PATH", "env")
        except subprocess.TimeoutExpired:
            return TestResult("OpenCode Installed", False, "Timeout", "env")

    # ─── Test Runner ─────────────────────────────────────────────────────────

    def run_all_tests(self) -> list[TestResult]:
        """Run all tests and return results."""
        tests = [
            # Config tests
            self.test_config_exists,
            self.test_model_configured,
            self.test_small_model_configured,
            # Agent tests
            self.test_rdev_agent_exists,
            self.test_quick_agent_exists,
            self.test_agent_tools_valid,
            # MCP tests
            self.test_github_mcp_enabled,
            self.test_essential_mcp_enabled,
            self.test_heavy_mcp_disabled,
            # Sync tests
            self.test_instructions_configured,
            self.test_agents_md_symlink,
            self.test_claude_md_exists,
            # Environment tests
            self.test_github_token_available,
            self.test_opencode_installed,
        ]

        self.results = []
        for test_fn in tests:
            log(f"Running: {test_fn.__doc__.split(':')[0].strip()}...")
            result = test_fn()
            self.results.append(result)
            level = "PASS" if result.passed else "FAIL"
            log(f"  {result.details}", level)

        return self.results


def generate_report(results: list[TestResult]) -> str:
    """Generate markdown test report."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    # Group by category
    categories = {}
    for r in results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r)

    report = f"""# OpenCode Agent Test Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tests:** {passed}/{total} passed ({100*passed//total}%)

## Summary

| Category | Passed | Total |
|----------|--------|-------|
"""

    for cat, cat_results in categories.items():
        cat_passed = sum(1 for r in cat_results if r.passed)
        report += f"| {cat.title()} | {cat_passed} | {len(cat_results)} |\n"

    report += f"\n## Detailed Results\n"

    for cat, cat_results in categories.items():
        report += f"\n### {cat.title()}\n\n"
        report += "| Test | Status | Details |\n"
        report += "|------|--------|--------|\n"
        for r in cat_results:
            status = "✅ Pass" if r.passed else "❌ Fail"
            # Escape pipe characters in details
            details = r.details.replace("|", "\\|")
            report += f"| {r.name} | {status} | {details} |\n"

    # Recommendations
    failures = [r for r in results if not r.passed]
    if failures:
        report += "\n## Recommendations\n\n"
        for r in failures:
            report += f"- **{r.name}**: {r.details}\n"
    else:
        report += "\n## 🎉 All Tests Passed!\n\n"
        report += "OpenCode Phase 2 configuration is complete and working.\n"

    return report


def main():
    print("=" * 60)
    print("🧪 OpenCode Agent Configuration Test Suite")
    print("=" * 60)
    print()

    tester = OpenCodeAgentTester()
    results = tester.run_all_tests()

    print()
    print("=" * 60)
    print("📊 Generating Report...")
    print("=" * 60)

    report = generate_report(results)

    # Save report
    report_path = Path(__file__).parent / "opencode_agent_report.md"
    report_path.write_text(report)
    print(f"\n📄 Report saved to: {report_path}")

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print()
    if passed == total:
        print("🎉 All tests passed! OpenCode agents are properly configured.")
        return 0
    else:
        print(f"⚠️  {total - passed}/{total} tests failed. See report for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
