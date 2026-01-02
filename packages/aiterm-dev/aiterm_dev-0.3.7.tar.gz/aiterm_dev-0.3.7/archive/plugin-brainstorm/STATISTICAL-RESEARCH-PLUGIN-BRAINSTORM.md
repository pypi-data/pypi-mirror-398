# Statistical Research Plugin Conversion - Brainstorm

**Generated:** 2025-12-23
**Purpose:** Convert statistical-research MCP → Plugin, remove R overlap with RForge

---

## 🎯 Core Insight

> **RForge already handles ALL R package development**
>
> Statistical-research MCP has 10 R-console tools that duplicate RForge functionality.
> The REAL value is in the 17 A-grade research skills + literature tools.
>
> **Solution:** Convert to plugin, remove R tools, focus on pure research workflows.

---

## 📊 Current State Analysis

### Statistical-Research MCP Tools (14 total)

#### R-Console Tools (10) ❌ REDUNDANT with RForge
- `r_execute` - Run R code
- `r_inspect` - Inspect R objects
- `r_test` - Run testthat tests
- `r_check` - Run R CMD check
- `r_coverage` - Code coverage
- `r_document` - Generate docs
- `r_lint` - Lint R code
- `r_plot` - Generate plots
- `r_preview` - Preview output
- `r_session` - Session management

**RForge equivalents:**
- RForge doesn't need these - it orchestrates at ecosystem level
- For actual R execution, use R console directly or RStudio
- RForge focuses on package coordination, not code execution

**Decision:** ❌ REMOVE - Not core research functionality

#### Literature Tools (5) ✅ KEEP - Core research value
- `arxiv_search` - Search arXiv
- `crossref_lookup` - DOI lookup
- `bibtex_search` - Search .bib files
- `bibtex_add` - Add bib entries
- `lit_note_create` - Create Obsidian notes

**Value:** Literature management is core to research workflow
**Decision:** ✅ KEEP - Convert to plugin commands

#### Skills (17 A-grade) ✅ KEEP - Highest value
- Mathematical (4): proof-architect, mathematical-foundations, identification-theory, asymptotic-theory
- Implementation (5): simulation-architect, algorithm-designer, numerical-methods, computational-inference, statistical-software-qa
- Writing (3): methods-paper-writer, publication-strategist, methods-communicator
- Research (5): literature-gap-finder, cross-disciplinary-ideation, method-transfer-engine, mediation-meta-analyst, sensitivity-analyst

**Value:** These are UNIQUE - no overlap with RForge
**Decision:** ✅ KEEP - Already skills, perfect for plugin

---

## 🏗️ Plugin Architecture Design

### Name: `statistical-research` Plugin (NOT MCP)
**Location:** `~/.claude/plugins/statistical-research/`

### Structure
```
statistical-research/
├── .claude-plugin/
│   └── plugin.json                    # Plugin metadata
├── commands/
│   ├── literature/
│   │   ├── arxiv-search.md           # Search arXiv
│   │   ├── crossref-lookup.md        # DOI lookup
│   │   ├── bibtex-search.md          # Search .bib files
│   │   ├── bibtex-add.md             # Add bib entries
│   │   └── lit-note.md               # Create Obsidian notes
│   ├── manuscript/
│   │   ├── methods-section.md        # Write methods section
│   │   ├── reviewer-response.md      # Respond to reviewers
│   │   └── proof-review.md           # Review mathematical proofs
│   ├── simulation/
│   │   ├── design.md                 # Simulation study design
│   │   └── analysis.md               # Analyze simulation results
│   └── research/
│       ├── lit-gap.md                # Find literature gaps
│       ├── hypothesis.md             # Formulate hypotheses
│       └── analysis-plan.md          # Create analysis plan
├── skills/                            # 17 A-grade skills (symlinked)
│   ├── mathematical/
│   │   ├── proof-architect.md
│   │   ├── mathematical-foundations.md
│   │   ├── identification-theory.md
│   │   └── asymptotic-theory.md
│   ├── implementation/
│   │   ├── simulation-architect.md
│   │   ├── algorithm-designer.md
│   │   ├── numerical-methods.md
│   │   ├── computational-inference.md
│   │   └── statistical-software-qa.md
│   ├── writing/
│   │   ├── methods-paper-writer.md
│   │   ├── publication-strategist.md
│   │   └── methods-communicator.md
│   └── research/
│       ├── literature-gap-finder.md
│       ├── cross-disciplinary-ideation.md
│       ├── method-transfer-engine.md
│       ├── mediation-meta-analyst.md
│       └── sensitivity-analyst.md
├── lib/
│   ├── arxiv-api.sh                   # arXiv API wrapper
│   ├── crossref-api.sh                # Crossref API wrapper
│   └── bibtex-utils.sh                # BibTeX utilities
└── README.md
```

---

## 📋 Slash Commands Design

### Literature Commands (5)
```markdown
/research:arxiv <query>
  Search arXiv for papers
  Returns: Title, authors, abstract, arXiv ID, PDF link

/research:doi <doi>
  Look up DOI, generate BibTeX
  Returns: Full citation, BibTeX entry

/research:bib:search <query>
  Search local .bib files
  Returns: Matching entries with keys

/research:bib:add <entry>
  Add entry to .bib file
  Interactive: Choose file, validate format

/research:lit:note <arxiv-id|doi>
  Create Obsidian literature note
  Template: Title, authors, abstract, key findings, notes
```

### Manuscript Commands (3)
```markdown
/research:manuscript:methods <topic>
  Draft methods section for statistical paper
  Uses: methods-paper-writer skill
  Returns: Structured methods section (LaTeX)

/research:manuscript:reviewer <review-file>
  Generate point-by-point reviewer response
  Parses reviewer comments, suggests responses

/research:manuscript:proof <theorem>
  Review mathematical proof for rigor
  Uses: proof-architect skill
```

### Simulation Commands (2)
```markdown
/research:simulation:design <method>
  Design Monte Carlo simulation study
  Uses: simulation-architect skill
  Returns: Simulation plan, scenarios, metrics

/research:simulation:analyze <results-file>
  Analyze simulation results
  Statistical summaries, visualizations
```

### Research Planning (3)
```markdown
/research:lit-gap <topic>
  Identify research gaps in literature
  Uses: literature-gap-finder skill
  Returns: Gap analysis, potential contributions

/research:hypothesis <context>
  Formulate testable hypotheses
  Uses: hypothesis-generator patterns

/research:analysis-plan <research-question>
  Create statistical analysis plan
  Returns: Step-by-step analysis workflow
```

**Total:** 13 slash commands (down from 14 MCP tools)

---

## 🎨 Multiple Implementation Approaches

### Approach 1: Pure Plugin (No MCP) ⭐⭐⭐⭐⭐ RECOMMENDED

**Architecture:**
- 13 slash commands (markdown + shell scripts)
- 17 skills (already exist, symlink)
- Shell scripts for API calls (arXiv, Crossref)
- No MCP server needed

**Pros:**
- ✅ Simpler architecture (no TypeScript/Bun)
- ✅ Faster to implement (markdown vs code)
- ✅ Easier to maintain (text files vs MCP protocol)
- ✅ Skills already exist (just organize)
- ✅ Clear separation (RForge = R dev, this = research)
- ✅ No R execution overlap

**Cons:**
- ❌ Can't execute R code directly (but that's the point!)
- ❌ Less programmatic control
- ❌ Limited to shell scripts for APIs

**Implementation Effort:** 1 week
- Day 1-2: Create plugin structure, move skills
- Day 3-4: Write 13 slash command markdown files
- Day 5: Shell scripts for arXiv/Crossref APIs
- Day 6-7: Test, document, polish

### Approach 2: Hybrid (Plugin Frontend + MCP Backend) ⭐⭐⭐

**Architecture:**
- Plugin with slash commands
- Lightweight MCP server for literature APIs only
- Skills in plugin
- R tools removed from MCP

**Pros:**
- ✅ Best of both (plugin UX + MCP power)
- ✅ TypeScript for complex API logic
- ✅ Shell scripts for simple commands

**Cons:**
- ❌ More complex (two layers)
- ❌ Still need MCP server running
- ❌ Higher maintenance

**Implementation Effort:** 2 weeks

### Approach 3: Keep MCP, Remove R Tools ⭐⭐

**Architecture:**
- Statistical-research MCP with only literature tools
- Remove all 10 R-console tools
- Skills stay as-is

**Pros:**
- ✅ Minimal changes
- ✅ MCP infrastructure already exists

**Cons:**
- ❌ Still using MCP for simple tasks
- ❌ Doesn't follow RForge plugin pattern
- ❌ Heavier architecture than needed

**Implementation Effort:** 2 days (just removal)

### Approach 4: Merge into RForge Orchestrator ⭐

**Architecture:**
- Add research commands to rforge-orchestrator plugin
- Becomes: R package dev + research workflows

**Pros:**
- ✅ Single plugin for all R-related work
- ✅ Unified mental model

**Cons:**
- ❌ Mixes concerns (dev vs research)
- ❌ Research isn't R-specific (applies to Python, etc.)
- ❌ RForge-orchestrator already has clear scope

**Implementation Effort:** 1 week

---

## 🔥 Recommended Approach: Pure Plugin (Approach 1)

### Why Pure Plugin?

**1. Clear Separation of Concerns**
- **RForge MCP:** R package ecosystem orchestration
- **Research Plugin:** Pure research workflows (language-agnostic)

**2. Follows Established Pattern**
- RForge showed plugin architecture works great
- Skills already exist (17 A-grade)
- Slash commands are intuitive

**3. Removes Redundancy**
- No R execution overlap with RForge
- Focus on research, not R tooling
- Literature + skills = core value

**4. Simpler Architecture**
- No MCP server to maintain
- Just markdown + shell scripts
- Easy to extend and modify

**5. Better User Experience**
- `/research:arxiv "mediation"` - clear intent
- Skills activate automatically
- Fast (no MCP protocol overhead)

---

## 📋 Migration Plan (Pure Plugin)

### Phase 1: Create Plugin Structure (Day 1)
```bash
cd ~/.claude/plugins
mkdir -p statistical-research/{.claude-plugin,commands/{literature,manuscript,simulation,research},skills,lib}

# Create plugin.json
cat > statistical-research/.claude-plugin/plugin.json <<'EOF'
{
  "name": "statistical-research",
  "version": "1.0.0",
  "description": "Statistical research workflows - literature management, manuscript writing, and 17 A-grade research skills",
  "author": {
    "name": "Stat-Wise",
    "email": "dt@stat-wise.com"
  }
}
EOF
```

### Phase 2: Move Skills (Day 2)
```bash
# Symlink existing skills from MCP to plugin
cd ~/.claude/plugins/statistical-research/skills
ln -s ~/projects/dev-tools/mcp-servers/statistical-research/skills/* .

# Or copy if symlinks cause issues
cp -r ~/projects/dev-tools/mcp-servers/statistical-research/skills/* .
```

### Phase 3: Create Literature Commands (Day 3)
**5 commands:** arxiv-search, crossref-lookup, bibtex-search, bibtex-add, lit-note

Example structure:
```markdown
<!-- commands/literature/arxiv-search.md -->
---
name: arxiv
description: Search arXiv for research papers
usage: /research:arxiv <query>
---

# arXiv Search

Search arXiv for research papers on statistical methods.

## Usage
\`\`\`
/research:arxiv "bootstrap mediation"
\`\`\`

## Implementation
Calls lib/arxiv-api.sh which uses arXiv API
Returns: Title, authors, abstract, PDF link

## Example
User: /research:arxiv "causal mediation"
Assistant: [Searches arXiv, presents top 10 papers with abstracts]
```

### Phase 4: Create Shell API Wrappers (Day 4)
```bash
# lib/arxiv-api.sh
#!/bin/bash
# arXiv API wrapper
query="$1"
max_results="${2:-10}"

curl -s "http://export.arxiv.org/api/query?search_query=${query}&max_results=${max_results}" \
  | xmllint --xpath "//entry" - \
  | parse_arxiv_xml

# lib/crossref-api.sh
#!/bin/bash
# Crossref API wrapper
doi="$1"

curl -s "https://api.crossref.org/works/${doi}" \
  | jq '.message | {title, author, DOI, publisher, published}'
```

### Phase 5: Create Manuscript Commands (Day 5)
**3 commands:** methods-section, reviewer-response, proof-review

These invoke existing skills with structured prompts.

### Phase 6: Create Simulation + Research Commands (Day 6)
**2 simulation + 3 research commands**

### Phase 7: Test & Document (Day 7)
- Test all 13 commands
- Write comprehensive README
- Create quick reference card
- Test skill activation

### Phase 8: Deprecate MCP (After testing)
```bash
# Remove statistical-research from Claude settings
# Edit ~/.claude/settings.json - remove mcpServers.statistical-research entry

# Archive MCP server
mv ~/projects/dev-tools/mcp-servers/statistical-research \
   ~/projects/dev-tools/mcp-servers/ARCHIVE/statistical-research-deprecated-2025-12-23
```

---

## 🎯 Benefits of Pure Plugin Approach

### Technical Benefits
1. **No R overlap** - RForge handles all R package work
2. **Language-agnostic** - Research applies to Python, Julia, etc.
3. **Simpler stack** - Markdown + bash vs TypeScript + MCP
4. **Faster** - No MCP protocol overhead
5. **Easier maintenance** - Text files vs code

### User Experience Benefits
1. **Clear mental model:**
   - RForge MCP = R package development & ecosystem
   - Research Plugin = Literature, manuscripts, skills
2. **Intuitive commands:**
   - `/research:arxiv` not `r_arxiv_search`
3. **Skills auto-activate** - No manual invocation
4. **Fast response** - Shell scripts vs MCP roundtrip

### Organizational Benefits
1. **Single plugin** - Not split across MCP + skills
2. **Follows pattern** - Like rforge-orchestrator
3. **Publishable** - Share with community
4. **Extensible** - Easy to add commands

---

## 📊 Comparison Matrix

| Aspect | Current (MCP) | Pure Plugin | Hybrid | Keep MCP |
|--------|---------------|-------------|--------|----------|
| R overlap with RForge | ❌ High (10 tools) | ✅ None | ✅ None | ❌ High |
| Architecture complexity | ⚠️ Medium | ✅ Simple | ❌ Complex | ⚠️ Medium |
| Implementation time | - | ✅ 1 week | ⚠️ 2 weeks | ✅ 2 days |
| Maintenance burden | ⚠️ Medium | ✅ Low | ❌ High | ⚠️ Medium |
| User experience | ⚠️ MCP tools | ✅ Slash commands | ✅ Slash commands | ⚠️ MCP tools |
| Skills integration | ✅ Excellent | ✅ Excellent | ✅ Excellent | ✅ Excellent |
| Literature APIs | ✅ TypeScript | ⚠️ Shell | ✅ TypeScript | ✅ TypeScript |
| Follows RForge pattern | ❌ No | ✅ Yes | ⚠️ Partial | ❌ No |

**Winner:** ✅ Pure Plugin

---

## 🚀 Recommended Implementation Plan

### Week 1: Build Pure Plugin
**Goal:** Convert statistical-research MCP → Plugin

**Days 1-2: Structure + Skills**
- Create plugin directory structure
- Move/symlink 17 A-grade skills
- Write plugin.json
- Create README

**Days 3-4: Literature Commands**
- Write 5 literature slash commands
- Create shell API wrappers (arXiv, Crossref)
- Test BibTeX search/add
- Test Obsidian note creation

**Days 5-6: Research Commands**
- Write 8 research/manuscript/simulation commands
- Integrate with skills
- Test end-to-end workflows

**Day 7: Test & Polish**
- Comprehensive testing
- Write quick reference card
- Document vs RForge separation
- Deploy to `~/.claude/plugins/`

### Week 2: Deprecate MCP (Optional)
**Goal:** Remove statistical-research MCP

**Day 1: Validate Plugin**
- Test all 13 commands work
- Verify skills activate correctly
- Confirm no RForge overlap

**Day 2: Remove MCP**
- Remove from `~/.claude/settings.json`
- Archive MCP server directory
- Update documentation

**Days 3-7: Buffer**
- Use new plugin for research work
- Fix any issues
- Refine based on usage

---

## 💡 Key Design Decisions

### Decision 1: Remove ALL R Tools ✅
**Rationale:** RForge handles R package orchestration comprehensively
**Impact:** No redundancy, clear separation

### Decision 2: Pure Plugin (No MCP) ✅
**Rationale:** Simpler, follows RForge pattern, easier to maintain
**Impact:** Markdown + shell vs TypeScript + MCP protocol

### Decision 3: Keep 17 Skills ✅
**Rationale:** Highest value, no overlap, already A-grade
**Impact:** Skills are core differentiator

### Decision 4: Focus on Research, Not Code Execution ✅
**Rationale:** Research workflows are language-agnostic
**Impact:** Useful beyond just R (Python, Julia, etc.)

### Decision 5: Slash Commands, Not MCP Tools ✅
**Rationale:** Better UX, clearer intent, faster
**Impact:** `/research:arxiv` vs `arxiv_search` tool

---

## 📚 Documentation Needed

### Plugin README.md
- Overview of plugin purpose
- Clear separation from RForge
- 13 command reference
- 17 skill descriptions
- Installation instructions
- Usage examples

### Quick Reference Card
- One-page command cheat sheet
- Skill activation patterns
- Common workflows

### Migration Guide (for MCP users)
- MCP → Plugin mapping
- New command syntax
- Skills migration (same)
- Configuration changes

---

## ⚠️ Risks & Mitigations

### Risk 1: Breaking Existing Workflows
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Keep MCP running during transition
- Test plugin thoroughly first
- Gradual migration over 2 weeks

### Risk 2: Shell Scripts Less Robust than TypeScript
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Comprehensive error handling
- Fallback to manual API calls
- Document shell script requirements

### Risk 3: Skill Activation Different
**Likelihood:** Low
**Impact:** Low
**Mitigation:**
- Skills work same in plugin as MCP
- Test activation patterns
- Document any differences

---

## ✅ Success Criteria

### Week 1 (Plugin Creation)
- [ ] Plugin structure created
- [ ] 17 skills moved/symlinked
- [ ] 13 slash commands written
- [ ] Shell API wrappers working
- [ ] All commands tested
- [ ] README complete

### Week 2 (MCP Deprecation - Optional)
- [ ] Plugin validated with real work
- [ ] MCP removed from settings
- [ ] MCP server archived
- [ ] Documentation updated
- [ ] No regressions vs MCP

### Long-term
- [ ] Plugin used regularly for research
- [ ] No R execution overlap with RForge
- [ ] Clear mental model (RForge = dev, Research = writing)
- [ ] Publishable to community

---

## 🎨 Final Recommendation

### ⭐⭐⭐⭐⭐ Build Pure Research Plugin

**Why:**
1. **Eliminates RForge overlap** - No R tools duplication
2. **Follows successful pattern** - RForge plugin architecture works
3. **Simpler architecture** - Markdown + shell vs MCP
4. **Better separation** - Dev (RForge) vs Research (Plugin)
5. **Language-agnostic** - Research applies beyond R

**Timeline:**
- **Week 1:** Build plugin (7 days)
- **Week 2:** Validate and optionally deprecate MCP
- **Effort:** ~15-20 hours total

**Value:**
- Clear mental model (RForge = R dev, Research = research)
- 13 useful slash commands
- 17 A-grade skills (already exist)
- No redundancy
- Publishable to community

**Next Step:**
1. Create plugin structure
2. Move skills
3. Write 13 commands (markdown)
4. Test
5. Use in real research work
6. Deprecate MCP when ready

---

**Status:** ✅ Brainstorm complete - Pure plugin recommended
**Next:** Create plugin structure and begin migration
