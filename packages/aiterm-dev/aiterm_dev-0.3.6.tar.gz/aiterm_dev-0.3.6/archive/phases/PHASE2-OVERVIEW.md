# Phase 2 Overview: R-Development MCP Consolidation

**Status:** Ready to execute
**Estimated Time:** 8-10 hours (can be split into 2-3 sessions)
**Risk:** Medium (renaming + code changes)
**Impact:** ⭐⭐⭐ High (consolidates 59% of your commands!)

---

## 🎯 The Big Idea

**Discovery from analysis:** 59% of your commands (35/59) are R-ecosystem related!

**Solution:** Consolidate ALL R functionality into one comprehensive MCP server:
- Rename `statistical-research` → `r-development` (better name!)
- Add 6 new R tools (ecosystem-health, pkgdown, manuscript, etc.)
- Migrate 10 R-related commands into the MCP
- Update 3 hub files (code.md, research.md, site.md)

**Result:**
- Commands: 49 → 36 files (-27% total, -22% from Phase 2 alone)
- MCP tools: 14 → 20 (+43% functionality!)
- One place for ALL R development needs

---

## 📋 Phase 2 Breakdown (4 Parts)

### Part A: Rename MCP Server (30 min)
**What:** Rename `statistical-research` → `r-development`

**Steps:**
1. Rename directory: `~/projects/dev-tools/mcp-servers/statistical-research` → `r-development`
2. Update `package.json` (name + description)
3. Update `~/.claude/settings.json` (mcpServers config)
4. Update `~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json` (browser extension)
5. Test MCP server still loads

**Files to modify:**
- `~/projects/dev-tools/mcp-servers/statistical-research/package.json`
- `~/.claude/settings.json`
- `~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json`

**Risk:** Low (just renaming, no code changes yet)

---

### Part B: Add 6 New Tools (4-5 hours)
**What:** Expand MCP from 14 → 20 tools

**New Tools:**

1. **`r_ecosystem_health`** (1 hour)
   - Health check for ALL MediationVerse packages
   - Runs r_check, r_test, r_coverage on entire ecosystem
   - Checks dependency graph
   - Generates comprehensive health report

2. **`r_package_check_quick`** (30 min)
   - Fast health check for single package
   - Combines existing tools (r_check, r_test, r_coverage)
   - Adds doc checks

3. **`pkgdown_build`** (1 hour)
   - Build R package documentation site
   - Wrapper around pkgdown::build_site()
   - Preview mode option

4. **`pkgdown_deploy`** (30 min)
   - Deploy pkgdown site to GitHub Pages
   - Wrapper around pkgdown::deploy_to_branch()

5. **`manuscript_section_writer`** (1.5 hours)
   - Draft manuscript sections (intro, methods, results, etc.)
   - Integrates with R analysis results
   - Zotero citations
   - LaTeX formatting for JASA/JSS/Biostatistics

6. **`reviewer_response_generator`** (30 min)
   - Point-by-point reviewer responses
   - Parses reviewer comments
   - Tracks manuscript changes
   - Generates structured response letter

**File to create/modify:**
- `~/projects/dev-tools/mcp-servers/r-development/src/tools/`
  - `r-console/ecosystem-health.ts` (new)
  - `r-console/package-check.ts` (extend existing)
  - `r-console/pkgdown.ts` (new)
  - `research/manuscript.ts` (new)
  - `research/reviewer-response.ts` (new)

**Risk:** Medium (new code, needs testing)

---

### Part C: Migrate 10 Commands (1 hour)
**What:** Archive commands that are now covered by MCP tools

**Commands to archive:**

From `~/.claude/commands/code/`:
- `ecosystem-health.md` → Use `r_ecosystem_health` tool
- `rpkg-check.md` → Use `r_package_check_quick` tool

From `~/.claude/commands/research/`:
- `cite.md` → Use `zotero_search`, `zotero_add` tools
- `manuscript.md` → Use `manuscript_section_writer` tool
- `revision.md` → Use `reviewer_response_generator` tool
- `lit-gap.md` → Use `literature_search` tool
- `method-scout.md` → Use `method_recommendations` tool
- `analysis-plan.md` → Use `create_analysis_plan` tool
- `sim-design.md` → Use `design_simulation` tool
- `hypothesis.md` → Use `hypothesis_generator` tool

**Commands:**
```bash
# Archive code commands
mv ~/.claude/commands/code/ecosystem-health.md ~/.claude/archive/
mv ~/.claude/commands/code/rpkg-check.md ~/.claude/archive/

# Archive research commands
mv ~/.claude/commands/research/cite.md ~/.claude/archive/
mv ~/.claude/commands/research/manuscript.md ~/.claude/archive/
mv ~/.claude/commands/research/revision.md ~/.claude/archive/
mv ~/.claude/commands/research/lit-gap.md ~/.claude/archive/
mv ~/.claude/commands/research/method-scout.md ~/.claude/archive/
mv ~/.claude/commands/research/analysis-plan.md ~/.claude/archive/
mv ~/.claude/commands/research/sim-design.md ~/.claude/archive/
mv ~/.claude/commands/research/hypothesis.md ~/.claude/archive/
```

**Risk:** Low (just moving files, backed up from Phase 1)

---

### Part D: Update 3 Hub Files (1 hour)
**What:** Update hub documentation to reference MCP tools

**Files to modify:**

1. **`~/.claude/commands/code.md`**
   - Add "R Package Development (via r-development MCP)" section
   - Reference new tools: `r_ecosystem_health`, `r_package_check_quick`

2. **`~/.claude/commands/research.md`**
   - Update to show all tools available via r-development MCP
   - Add new manuscript tools section
   - Remove individual command references

3. **`~/.claude/commands/site.md`**
   - Add "R Package Documentation" section
   - Reference pkgdown tools
   - Distinguish from MkDocs (Python/Node)

**Risk:** Low (just documentation updates)

---

## 🎯 Success Criteria

After Phase 2 completion:

✅ **MCP server renamed and working**
- `r-development` loads in Claude Code
- All 14 existing tools still work
- Settings updated in both Desktop and Browser configs

✅ **6 new tools implemented**
- All tools have proper TypeScript definitions
- All tools tested manually
- Documentation updated

✅ **10 commands archived**
- Files moved to `~/.claude/archive/`
- No active references to deprecated commands
- Hub files updated to guide users to MCP

✅ **Documentation complete**
- 3 hub files updated
- PHASE2-COMPLETION.md created
- .STATUS updated

✅ **Final state**
- Commands: 49 → 36 files (-27% total)
- MCP tools: 14 → 20 (+43%)
- One comprehensive R development toolkit

---

## 💡 Recommended Execution Strategy

### Session 1 (2-3 hours): Rename + First 2 Tools
1. Part A: Rename MCP server (30 min)
2. Tool 1: `r_ecosystem_health` (1 hour)
3. Tool 2: `r_package_check_quick` (30 min)
4. Test everything works
5. Commit progress

### Session 2 (2-3 hours): Pkgdown Tools
1. Tool 3: `pkgdown_build` (1 hour)
2. Tool 4: `pkgdown_deploy` (30 min)
3. Test with actual R package
4. Commit progress

### Session 3 (3-4 hours): Manuscript Tools + Cleanup
1. Tool 5: `manuscript_section_writer` (1.5 hours)
2. Tool 6: `reviewer_response_generator` (30 min)
3. Part C: Archive 10 commands (1 hour)
4. Part D: Update 3 hubs (1 hour)
5. Final testing + documentation
6. Commit + celebrate! 🎉

**Key:** Each session has clear stopping points. ADHD-friendly!

---

## 🚨 Potential Challenges

1. **TypeScript compilation errors**
   - Solution: Test incrementally, one tool at a time

2. **R code execution issues**
   - Solution: Test R commands manually in RStudio first

3. **Zotero integration complexity**
   - Solution: Start simple, enhance later

4. **Testing without breaking existing tools**
   - Solution: Create test suite, run before each commit

---

## 📚 References

- **Full Plan:** `REFACTORING-ACTION-PLAN-REVISED.md`
- **Analysis:** `COMMAND-MCP-REFACTORING-ANALYSIS-REVISED.md`
- **MCP Server Location:** `~/projects/dev-tools/mcp-servers/statistical-research/`
- **Commands Location:** `~/.claude/commands/`
- **Settings:** `~/.claude/settings.json`, `~/projects/dev-tools/claude-mcp/MCP_SERVER_CONFIG.json`

---

## Next Action

When ready to start Phase 2:

```bash
# 1. Read this overview
cat PHASE2-OVERVIEW.md

# 2. Review full plan
cat REFACTORING-ACTION-PLAN-REVISED.md | less +/Phase\ 2

# 3. Start Session 1
# (I'll be ready to help!)
```

**Recommended:** Start fresh, with focused energy. Phase 2 is more complex than Phase 1!
