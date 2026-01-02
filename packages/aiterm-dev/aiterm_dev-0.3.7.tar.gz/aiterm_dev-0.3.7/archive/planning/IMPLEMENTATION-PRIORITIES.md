# Implementation Priorities

**Date:** 2025-12-20 (Updated: 2025-12-26)
**Purpose:** Prioritize next features for aiterm
**Status:** v0.2.1 released, planning v0.3.0

---

## ✅ COMPLETED: Distribution (v0.2.1)

- [x] PyPI publishing (`pip install aiterm-dev`)
- [x] Homebrew distribution (`brew install data-wise/tap/aiterm`)
- [x] GitHub Actions trusted publishing
- [x] Documentation standards (9 REFCARDs)
- [x] CLI improvements (19 commands with epilogs)

---

## 🎯 CURRENT PRIORITY: v0.3.0 Planning

**Options for v0.3.0:**
1. **Gemini CLI Support** - Multi-tool integration
2. **IDE Integrations** - Positron, Zed, VS Code extensions
3. **Workflow Automation** - Enhanced /workflow commands
4. **R-Development MCP** - Consolidate R ecosystem tools

---

## Historical: Documentation First! (Dec 21, 2025)

**Based on RForge Success:**
After completing comprehensive RForge auto-detection documentation (7 docs, ~80 pages, 15 diagrams), we've validated a critical insight:

> **Comprehensive documentation BEFORE broad feature expansion prevents confusion and accelerates development.**

**NEW PHASE 0 (Before Implementation):**
- Create complete aiterm documentation suite (API, Architecture, Guides)
- 20+ Mermaid diagrams for system design
- 60+ code examples
- Deploy to GitHub Pages

**Timeline:** 3 weeks for complete docs
**Benefits:**
- ✅ Clarifies vision before coding
- ✅ Prevents scope creep
- ✅ Guides development (docs as spec)
- ✅ Accelerates onboarding (users + developers)
- ✅ Reduces future support burden

**See:** `DOCUMENTATION-PLAN.md` for complete plan

**Then proceed with implementation priorities below...**

---

## The Big Question

**Should we focus on:**
- **A) RForge-only** (5 R package ideation tools)
- **B) Broader scope** (15 workflows + 10 ideation tools)
- **C) Hybrid** (Start narrow, expand later)

---

## Analysis: RForge-Only vs Broader

### Option A: RForge-Only (Recommended ⭐)

**What:** Implement 5 RForge ideation tools only
- `rforge:plan`
- `rforge:plan:quick-fix`
- `rforge:plan:new-package`
- `rforge:plan:vignette`
- `rforge:plan:refactor`

**Pros:**
- ✅ **Focused** - One domain (R packages) you use daily
- ✅ **Fast** - 5 tools vs 25 tools (5x faster to MVP)
- ✅ **Testable** - You have real R package work to validate
- ✅ **Learning** - Refine pattern before scaling
- ✅ **Dopamine** - Working tool in 1-2 weeks vs 2-3 months

**Cons:**
- ❌ Doesn't help with teaching/research workflows
- ❌ Doesn't help with dev-tools workflows
- ❌ Missing broader ideation (architecture, integration, etc.)

**Time to MVP:** 1-2 weeks
**ADHD Fit:** 🧠🧠🧠🧠🧠 (excellent - focused, achievable)

---

### Option B: Broader Scope

**What:** Implement all 25 tools (15 workflows + 10 ideation)

**Pros:**
- ✅ Complete solution for all workflows
- ✅ Helps with teaching, research, dev-tools
- ✅ More impressive for public release

**Cons:**
- ❌ **Overwhelming** - 25 tools is a LOT
- ❌ **Slow** - 2-3 months minimum to MVP
- ❌ **Risk** - Might abandon before finishing (ADHD concern)
- ❌ **Untested** - Won't validate patterns until much later
- ❌ **Scope creep** - Will keep expanding

**Time to MVP:** 2-3 months
**ADHD Fit:** 🧠 (poor - too big, high abandonment risk)

---

### Option C: Hybrid (Start Narrow, Expand)

**What:**
1. **Phase 1 (Week 1-2):** Core RForge ideation
   - `rforge:plan` (the main tool)
   - `rforge:plan:quick-fix` (fast iterations)

2. **Phase 2 (Week 3-4):** Test & Refine
   - Use on real R package work
   - Refine conversation flow
   - Adjust based on actual usage

3. **Phase 3 (Week 5-6):** Expand RForge
   - `rforge:plan:new-package`
   - `rforge:plan:vignette`
   - `rforge:plan:refactor`

4. **Phase 4 (Month 2+):** Generalize pattern
   - Extract core ideation engine
   - Add teaching workflows
   - Add research workflows
   - Add dev-tools workflows

**Pros:**
- ✅ **Progressive** - Quick win → validation → expansion
- ✅ **Risk mitigation** - Small investment to validate
- ✅ **Learning** - Refine pattern with real usage
- ✅ **Momentum** - Working tool fast, builds confidence
- ✅ **ADHD-friendly** - Achievable milestones

**Cons:**
- ❌ Doesn't immediately solve all workflow needs
- ❌ Requires discipline to stick to phases

**Time to MVP:** 1-2 weeks (Phase 1), then iterate
**ADHD Fit:** 🧠🧠🧠🧠🧠 (excellent - best of both worlds)

---

## Recommendation: Option C (Hybrid) ⭐⭐⭐

**Start with 2 core RForge tools:**
1. `rforge:plan` - Main ideation
2. `rforge:plan:quick-fix` - Quick iterations

**Why these 2?**
- **80/20 Rule:** These handle 80% of your R package planning needs
- **Complementary:** One for new work, one for fixes
- **Testable:** You have real use cases NOW
- **Fast:** 1-2 weeks to working prototype
- **Validating:** Proves the conversational pattern works

**Then decide:**
- If they work well → expand to other 3 RForge tools
- If pattern needs work → refine before expanding
- If you love them → generalize to teaching/research/dev-tools

---

## Detailed Priority Ranking

### Tier 1: Must Have (Implement First) ⭐⭐⭐

#### 1. `rforge:plan` (Core Ideation)
**Score: 10/10**
- **Value:** Highest - solves vague idea → clear spec
- **Frequency:** Daily (you plan R package work constantly)
- **ADHD Impact:** Massive - prevents overthinking spiral
- **Complexity:** Medium (5 questions, 2 options, spec generation)
- **Dependencies:** None (standalone)
- **Time to build:** 1 week

**Why first:**
- Most valuable tool
- Validates entire ideation pattern
- Everything else builds on this

---

#### 2. `rforge:plan:quick-fix` (Bug Fix Planning)
**Score: 9/10**
- **Value:** High - fast iteration on bug fixes
- **Frequency:** Weekly (bugs happen!)
- **ADHD Impact:** High - ultra-fast (< 1 min), instant action
- **Complexity:** Low (3 questions, no spec doc)
- **Dependencies:** None (standalone)
- **Time to build:** 2-3 days

**Why second:**
- Quick win (builds on rforge:plan pattern)
- Different use case (validates pattern flexibility)
- High frequency need

---

### Tier 2: Should Have (Implement After Validation) ⭐⭐

#### 3. `rforge:plan:new-package` (Package Creation)
**Score: 7/10**
- **Value:** Medium-High - helps start new packages correctly
- **Frequency:** Monthly (you create packages occasionally)
- **ADHD Impact:** Medium - prevents analysis paralysis on new projects
- **Complexity:** Medium (package structure, templates)
- **Dependencies:** Package templates
- **Time to build:** 1 week

**Why third:**
- Less frequent but high value when needed
- More complex (needs templates)
- Can wait until pattern validated

---

#### 4. `rforge:plan:vignette` (Documentation Planning)
**Score: 6/10**
- **Value:** Medium - helps with documentation planning
- **Frequency:** Monthly (vignettes added occasionally)
- **ADHD Impact:** Medium - structures writing task
- **Complexity:** Low (outline generation)
- **Dependencies:** None
- **Time to build:** 3-4 days

**Why fourth:**
- Nice to have, not critical
- Simple to implement
- Lower frequency

---

#### 5. `rforge:plan:refactor` (Code Cleanup Planning)
**Score: 6/10**
- **Value:** Medium - helps with safe refactoring
- **Frequency:** Quarterly (refactoring is periodic)
- **ADHD Impact:** High - prevents "rewrite everything" impulse
- **Complexity:** High (code analysis, risk assessment)
- **Dependencies:** Code complexity analysis tools
- **Time to build:** 1-2 weeks

**Why fifth:**
- Highest complexity
- Lowest frequency
- Can be done manually for now

---

### Tier 3: Nice to Have (Future) ⭐

#### Workflow Commands (15 total)
**Score: Variable (4-8/10)**
- **Value:** High when implemented
- **Complexity:** Varies by workflow
- **ADHD Impact:** High (automation is always good)
- **Dependencies:** Requires execution tools (rforge:pkg:*, etc.)

**Why later:**
- Need planning tools first (cart before horse)
- Need execution infrastructure
- Can be built incrementally

---

#### General DevOps Ideation (10 tools)
**Score: Variable (5-7/10)**
- **Value:** Medium-High
- **Complexity:** High (broad domain knowledge)
- **ADHD Impact:** Medium-High
- **Dependencies:** Cross-domain understanding

**Why later:**
- Less focused (broader scope)
- After RForge pattern validated
- Can extract from RForge learnings

---

## Implementation Roadmap

### Phase 1: Core RForge Ideation (Weeks 1-2) ⭐ DO THIS

**Goal:** Prove the conversational ideation pattern works

**Deliverables:**
1. `rforge:plan` - Functional prototype
   - 5-question conversation flow
   - 2-option proposal
   - Spec document generation
   - File save/organization

2. `rforge:plan:quick-fix` - Functional prototype
   - 3-question ultra-fast flow
   - Direct-to-action (no spec doc)
   - Integration with existing tools

**Success Criteria:**
- [ ] Used `rforge:plan` for 3+ real R package ideas
- [ ] Specs generated are clear and actionable
- [ ] Time from idea → spec is < 5 minutes
- [ ] You actually use it (not just build it!)
- [ ] `rforge:plan:quick-fix` used for 3+ bug fixes
- [ ] Bug fix planning takes < 1 minute

**Time Budget:** 1-2 weeks
**Output:** 2 working tools + usage validation

---

### Phase 2: Validation & Refinement (Week 3)

**Goal:** Refine based on real usage

**Activities:**
1. Use rforge:plan for all new R package work
2. Track friction points
3. Adjust questions/options
4. Improve spec templates
5. Add missing features

**Success Criteria:**
- [ ] Tools feel natural to use
- [ ] 5-minute goal met consistently
- [ ] Spec documents are useful (actually reference them!)
- [ ] ADHD features working (quick wins, clear options, etc.)

**Time Budget:** 1 week of active usage
**Output:** Refined tools + lessons learned

---

### Phase 3: Expand RForge (Weeks 4-6)

**Goal:** Complete RForge ideation suite

**Deliverables:**
1. `rforge:plan:new-package` (Week 4)
2. `rforge:plan:vignette` (Week 5)
3. `rforge:plan:refactor` (Week 6)

**Success Criteria:**
- [ ] All 5 RForge tools working
- [ ] Consistent pattern across tools
- [ ] Used in real scenarios
- [ ] Documentation complete

**Time Budget:** 3 weeks
**Output:** Complete RForge ideation suite

---

### Phase 4: Generalize Pattern (Month 2+)

**Goal:** Extract core pattern, apply to other domains

**Activities:**
1. Extract ideation engine (core conversation logic)
2. Create domain adapters (R packages, teaching, research, dev-tools)
3. Implement teaching workflows
4. Implement research workflows
5. Implement dev-tools workflows

**Success Criteria:**
- [ ] Core engine reusable
- [ ] 3+ domains supported
- [ ] Pattern validated across domains

**Time Budget:** 4-6 weeks
**Output:** General-purpose ideation system

---

## Resource Allocation

### Time Commitment

**Phase 1 (Weeks 1-2):**
- **Week 1:** Build `rforge:plan` (10-15 hours)
  - Day 1-2: Conversation flow (4 hours)
  - Day 3-4: Option generation (4 hours)
  - Day 5-6: Spec generation (4 hours)
  - Day 7: Testing & refinement (3 hours)

- **Week 2:** Build `rforge:plan:quick-fix` (5-8 hours)
  - Day 1-2: Fast conversation flow (3 hours)
  - Day 3-4: Direct action integration (3 hours)
  - Day 5: Testing (2 hours)

**Total Phase 1:** 15-23 hours over 2 weeks (manageable!)

---

### Complexity Assessment

**Tier 1 (Straightforward):**
- Conversation flow (text prompts)
- Option templates (markdown generation)
- File I/O (save specs)

**Tier 2 (Medium):**
- Context analysis (detecting similar code)
- Time estimation (predicting work hours)
- Integration with existing tools

**Tier 3 (Complex):**
- Code complexity analysis (for refactor tool)
- Cross-package dependency scanning (for cascade tool)
- Intelligent defaults (learning from past choices)

**Phase 1 uses only Tier 1-2 complexity** → Achievable!

---

## Risk Assessment

### High Risk (Avoid)
❌ **Building all 25 tools** - Too big, will abandon
❌ **Perfect spec templates** - Overthinking, analysis paralysis
❌ **AI-generated options** - Complex, might not be useful

### Medium Risk (Mitigate)
⚠️ **5-question format too rigid** - Mitigation: Allow skipping questions
⚠️ **Time estimates inaccurate** - Mitigation: Wide ranges, learn over time
⚠️ **Specs not used** - Mitigation: Test with real work early

### Low Risk (Accept)
✅ **Pattern needs refinement** - Expected, Phase 2 handles this
✅ **Not all features used** - Fine, keep what works
✅ **Manual fallback needed** - Good to have escape hatch

---

## Decision Framework

### Use this to decide on additional tools:

**Scoring (0-10 for each):**
1. **Value** - How useful is this?
2. **Frequency** - How often will I use it?
3. **ADHD Impact** - Does it solve an ADHD-specific problem?
4. **Complexity** - How hard to build? (10 = easy, 0 = hard)
5. **Dependencies** - Can it be built standalone? (10 = yes, 0 = no)

**Formula:**
```
Priority Score = (Value + Frequency + ADHD Impact + Complexity + Dependencies) / 5
```

**Cutoffs:**
- **9-10:** Must have (Tier 1)
- **7-8:** Should have (Tier 2)
- **5-6:** Nice to have (Tier 3)
- **< 5:** Skip for now

**Example:**
```
rforge:plan
- Value: 10
- Frequency: 10
- ADHD Impact: 10
- Complexity: 6
- Dependencies: 8
= 44/5 = 8.8 (Must have!)

rforge:plan:refactor
- Value: 7
- Frequency: 4
- ADHD Impact: 8
- Complexity: 3
- Dependencies: 4
= 26/5 = 5.2 (Nice to have, but lower priority)
```

---

## Questions to Answer Before Starting

### 1. Technical Foundation
**Q:** What infrastructure exists?
**A:** Need to check:
- RForge MCP server structure
- Tool definition format
- Conversation handling (stdin/stdout?)
- File I/O patterns
- Integration with existing RForge tools

**Action:** Review existing MCP servers (statistical-research, shell, project-refactor)

---

### 2. Conversation Interface
**Q:** How should users interact?
**Options:**
- **A) CLI prompts** (simple, works everywhere)
- **B) Web UI** (prettier, more complex)
- **C) Chat-style** (conversational, but needs more infra)

**Recommendation:** Start with CLI prompts (simplest)

---

### 3. Spec Storage
**Q:** Where to save specs?
**Options:**
- **A) `~/PROPOSALS/`** (global, all projects)
- **B) `{project}/proposals/`** (project-specific)
- **C) Both** (save to both)

**Recommendation:** Option C (both)
- Global for cross-project reference
- Project-specific for context

---

### 4. Option Generation
**Q:** How to generate options?
**Options:**
- **A) Template-based** (predefined patterns)
- **B) AI-generated** (dynamic, complex)
- **C) Hybrid** (templates + customization)

**Recommendation:** Start with A (templates), evolve to C

---

### 5. Time Estimation
**Q:** How to estimate time?
**Options:**
- **A) Static rules** (simple function = 1 hour)
- **B) Historical data** (learn from past)
- **C) User input** (ask user to estimate)

**Recommendation:** Start with A, add B over time

---

## Summary & Recommendation

### 🎯 Recommended Path: Hybrid Approach

**Phase 1 (Weeks 1-2): Build 2 Core Tools**
1. `rforge:plan` - Main ideation (1 week)
2. `rforge:plan:quick-fix` - Fast iterations (3-4 days)

**Phase 2 (Week 3): Validate**
- Use tools on real R package work
- Refine based on friction points
- Decide on next tools

**Phase 3 (Weeks 4-6): Expand if successful**
- Add remaining 3 RForge tools
- OR pivot if pattern needs work

**Phase 4 (Month 2+): Generalize**
- Extract core pattern
- Apply to teaching/research/dev-tools

### Why This Works (ADHD-Friendly)

✅ **Quick Win** - Working tool in 1-2 weeks
✅ **Validation** - Test before expanding
✅ **Achievable** - 2 tools, not 25
✅ **Momentum** - Success builds confidence
✅ **Flexible** - Can adjust based on learnings
✅ **Focused** - One domain (R packages) you know well

### Success Metrics

**After Phase 1:**
- [ ] Used `rforge:plan` 3+ times
- [ ] Specs took < 5 minutes
- [ ] Specs were actionable
- [ ] You want to keep using it!

**If metrics met:** Continue to Phase 3
**If not met:** Refine in Phase 2

---

## Next Steps

**Immediate (Today):**
1. Review this prioritization
2. Decide: Agree with hybrid approach?
3. If yes: Proceed to technical design for `rforge:plan`

**This Week:**
1. Design conversation flow (5 questions)
2. Create option templates (Quick/Balanced)
3. Design spec document format
4. Start implementation

**Decision Point:**
Do you agree with the hybrid approach? Or prefer RForge-only or broader scope?

---

**Status:** Ready for your decision! 🚀
