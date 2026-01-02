# RForge Ideation & Planning Tools - ADHD-Friendly Design

> **STATUS: IMPLEMENTED**
> **Date:** 2025-12-27
> **Version:** v0.1.0
> The tools `rforge_plan` and `rforge_plan_quick_fix` have been implemented in the RForge MCP server.

## Core Tool: `rforge:plan`

**Purpose:** Turn vague R package idea into clear specification

**Single Command Interface:**
```bash
rforge:plan "I want to add sensitivity analysis to RMediation"
```

### Conversation Flow (FAST!)

**Step 1: Rapid-Fire Questions (2 minutes)**
```
Tool: "Got it! 5 quick questions:

1. Scope?
   [a] One function  [b] Small feature  [c] Major feature
   →

2. Users?
   [a] Just you  [b] MediationVerse users  [c] General R users
   →

3. Timeline?
   [a] Today (1-2 hours)  [b] This week  [c] This month
   →

4. Complexity OK?
   [a] Simple (like existing code)  [b] Medium (new patterns)  [c] Complex (research needed)
   →

5. Breaking changes OK?
   [a] No (backward compatible)  [b] Maybe (if worth it)  [c] Yes (major version)
   →
"
```

**Step 2: Auto-Analysis (30 seconds - no user input)**
```
Analyzing...
✓ Similar code: sensitivity.R (125 lines)
✓ Dependencies: RMediation, boot
✓ Test coverage: 85% (good foundation)
✓ Documentation: roxygen2 ready
✓ Impact: RMediation only (low risk)
```

**Step 3: 2 Clear Options (not 5, not 10!)**
```
Based on your answers, here are 2 paths:

┌─────────────────────────────────────────────────┐
│ Option A: Quick & Simple ⚡                     │
├─────────────────────────────────────────────────┤
│ What: Add ci_sensitivity() to RMediation       │
│ Time: 1-2 hours TODAY                          │
│ Complexity: ⭐ (matches existing pattern)      │
│ ADHD: 🧠🧠🧠🧠🧠 (perfect!)                      │
│                                                 │
│ You get:                                        │
│ • One new function                              │
│ • Bootstrap sensitivity intervals               │
│ • Works like ci_mediation()                     │
│ • Quick dopamine win!                           │
│                                                 │
│ You don't get:                                  │
│ • Multiple sensitivity methods                  │
│ • Fancy visualizations                          │
│ • Separate package                              │
│                                                 │
│ Next: Copy ci_mediation() → modify → test → ✓  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Option B: Proper Feature 🔧                     │
├─────────────────────────────────────────────────┤
│ What: Full sensitivity analysis module          │
│ Time: 1 week                                    │
│ Complexity: ⭐⭐⭐ (new patterns, research)      │
│ ADHD: 🧠🧠🧠 (manageable with breaks)            │
│                                                 │
│ You get:                                        │
│ • Multiple methods (Sobel, bootstrap, Bayes)    │
│ • Sensitivity plots                             │
│ • Vignette                                      │
│ • Publication-ready                             │
│                                                 │
│ You don't get:                                  │
│ • Quick dopamine (takes time)                   │
│ • Simple codebase (more complexity)             │
│                                                 │
│ Next: Research → design → implement → test      │
└─────────────────────────────────────────────────┘

Which path? [A/B] (recommended: A for quick win)
```

**Step 4: Generate Spec (30 seconds - automated)**
```
User picks: A

Generating spec...
✓ Created: ~/PROPOSALS/RFORGE-sensitivity-quick-2025-12-20.md
✓ Created: ~/TODO/RMediation-sensitivity.md (task list)

Next steps:
1. Open RMediation project
2. Run: rforge:pkg:scaffold function ci_sensitivity
3. Copy pattern from ci_mediation()
4. Code! (1-2 hours)

Ready to start? [Y/n]
```

---

## Spec Document Format (ADHD-Optimized)

**File:** `RFORGE-{feature}-{approach}-{date}.md`

### Template Structure

```markdown
# Feature: {Name}

**Status:** 📝 Planned
**Timeline:** {Today/This Week/This Month}
**Complexity:** {⭐-⭐⭐⭐}
**ADHD Rating:** {🧠-🧠🧠🧠🧠🧠}

---

## 🎯 What You're Building

{One sentence - super clear}

## ⏱️ Time Budget

**Total:** {1-2 hours / 1 day / 1 week}
**Sessions:** {1 / 2-3 / 5-10}
**Per Session:** {30 min / 1-2 hours}

## ✅ You Get

- {Specific deliverable 1}
- {Specific deliverable 2}
- {Specific deliverable 3}

## ❌ You Don't Get (Scope Boundary!)

- {Out of scope 1}
- {Out of scope 2}
- {Future enhancement}

## 📋 Task Breakdown

### Session 1: {Focus} (⏱️ {time})
- [ ] {Concrete task 1}
- [ ] {Concrete task 2}
- [ ] {Concrete task 3}
- [ ] ✓ Checkpoint: {What should work}

### Session 2: {Focus} (⏱️ {time})
- [ ] {Concrete task 1}
- [ ] {Concrete task 2}
- [ ] ✓ Checkpoint: {What should work}

## 🚀 Quick Start

```r
# First thing to do:
{exact command to run}
```

## 📚 Reference Code

**Similar pattern:** `{file}:{line_range}`
**Copy from:** `{specific function}`

## 🎉 Done Criteria

You're done when:
1. {Specific outcome 1}
2. {Specific outcome 2}
3. {Specific outcome 3}

## 💡 If You Get Stuck

**Common issues:**
- {Issue 1} → {Solution}
- {Issue 2} → {Solution}

**Ask for help:** rforge:help {topic}
```

---

## Supporting Tools (5 Total)

### 1. `rforge:plan` (Core Tool - described above)
**When:** Starting any new R package work
**Time:** 5 minutes
**Output:** Specification document + task list

---

### 2. `rforge:plan:quick-fix`
**Purpose:** Plan a quick bug fix (< 1 hour)

**Ultra-Fast Flow:**
```bash
rforge:plan:quick-fix "ci_mediation returns NA for large datasets"

# 3 questions only:
1. Which package? [auto-detect from git]
2. Severity? [low/medium/high]
3. Fix now or later? [now/later]

# Output (30 seconds):
✓ Issue: {description}
✓ Location: {file}:{line} (best guess)
✓ Approach: {1-2 sentence fix strategy}
✓ Tests: {which tests to run}
✓ Time: {15 min / 30 min / 1 hour}

Start? [Y/n]
```

**ADHD Feature:** No spec document! Just quick guidance + start coding.

---

### 3. `rforge:plan:new-package`
**Purpose:** Plan new package in MediationVerse

**Questions (2 minutes):**
```
1. Package name?
2. Core functionality? (1 sentence)
3. Standalone or depends on others? [standalone/depends]
4. Timeline? [quick/standard/research]
5. Template? [minimal/standard/full]
```

**Output:**
- Package structure spec
- Dependency analysis (if depends on others)
- DESCRIPTION template
- First 3 functions to implement
- Test strategy

**Time:** 5-7 minutes total

---

### 4. `rforge:plan:vignette`
**Purpose:** Plan a new package vignette

**Questions (1 minute):**
```
1. Topic? (e.g., "Getting Started", "Advanced Usage")
2. Audience? [beginners/researchers/developers]
3. Length? [short 5-10 min read / medium 20 min / long 30+ min]
4. Examples from? [create new / use existing]
```

**Output:**
- Vignette outline (sections)
- Code examples to include
- Estimated writing time
- Template file

**Time:** 3-5 minutes total

---

### 5. `rforge:plan:refactor`
**Purpose:** Plan refactoring without breaking things

**Questions (2 minutes):**
```
1. What code to refactor? [file/function]
2. Why? [a) hard to understand  b) slow  c) duplicated  d) ugly]
3. Risk tolerance? [a) can't break anything  b) some risk OK]
4. Time budget? [a) 1 hour  b) 1 day  c) 1 week]
```

**Analysis (automated):**
- Current code complexity
- Test coverage
- Who uses this code (reverse deps)
- Risk level (🔴🟡🟢)

**Output:**
- Refactoring strategy (Strangler Fig / Big Bang / Extract)
- Step-by-step safety plan
- Test requirements
- Rollback plan

**Time:** 5-10 minutes total

---

## ADHD-Friendly Features (All Tools)

### 1. **Minimal Decisions**
- Max 5 questions, usually 2-3
- Multiple choice (a/b/c) not free text
- Smart defaults (just press Enter)
- Auto-detect context when possible

### 2. **Quick Wins Highlighted**
```
Option A: Quick & Simple ⚡ ← THIS ONE!
Time: 1-2 hours TODAY
ADHD: 🧠🧠🧠🧠🧠

Option B: Comprehensive 🔧
Time: 1 week
ADHD: 🧠🧠🧠
```

### 3. **Dopamine Planning**
- Time estimates for everything
- Session breakdown (digestible chunks)
- Checkpoint system (mini celebrations)
- Progress visualization

### 4. **No Lost Context**
- Everything saved to files
- Resume later (state preservation)
- Clear "done" criteria
- Reference code linked

### 5. **Escape Hatches**
- `Ctrl+C` → saves state
- "Not sure?" → skip question (use default)
- "Too complex?" → suggests simpler option
- "Stuck?" → built-in help

### 6. **Visual Clarity**
- Boxes around options
- Emoji for quick scanning (⚡🔧🧠✓❌)
- Color coding (if terminal supports)
- Clear hierarchy (headers, bullets)

---

## Integration with RForge Execution Tools

**Planning → Execution Flow:**

```
rforge:plan → generates spec
    ↓
spec includes exact commands
    ↓
rforge:pkg:scaffold function {name}
    ↓
{work happens}
    ↓
rforge:pkg:test
    ↓
Done! ✓
```

**Example:**
```bash
# Planning (5 min)
$ rforge:plan "add ci_sensitivity to RMediation"
→ Creates: RFORGE-sensitivity-quick-2025-12-20.md
→ Says: "Run: rforge:pkg:scaffold function ci_sensitivity"

# Execution (1 hour)
$ rforge:pkg:scaffold function ci_sensitivity
→ Creates function skeleton
→ Copies pattern from ci_mediation()

# {You code for 45 min}

# Testing (10 min)
$ rforge:pkg:test ci_sensitivity
→ Runs tests
→ Shows coverage
→ ✓ All pass!

# Done! 🎉
Total time: 1h 15min (spec said 1-2 hours) ✓
```

---

## File Organization (ADHD-Friendly)

### All specs in one place:
```
~/PROPOSALS/
├── RFORGE-sensitivity-quick-2025-12-20.md
├── RFORGE-new-pkg-medtest-2025-12-19.md
├── RFORGE-refactor-boot-2025-12-18.md
└── ...
```

### Task lists (optional):
```
~/TODO/
├── RMediation-sensitivity.md
├── medtest-package.md
└── ...
```

### Completed (archive):
```
~/PROPOSALS/archive/
├── RFORGE-ci-mediation-2025-11-01.md ✓
└── ...
```

**ADHD Benefit:** Everything in one place, easy to find, clear status.

---

## Comparison: Traditional vs ADHD-Friendly

### Traditional Approach:
```
1. Have vague idea
2. Think about it for days
3. Forget details
4. Start coding anyway
5. Realize halfway through it's too complex
6. Abandon or struggle
7. Feel bad
```
**Time:** Days of thinking + hours of confused coding = 😫

### RForge ADHD-Friendly Approach:
```
1. Have vague idea
2. Run: rforge:plan "{idea}"
3. Answer 5 questions (2 min)
4. Get 2 clear options
5. Pick one (30 sec)
6. Get spec + task list
7. Start coding! (dopamine!)
```
**Time:** 5 minutes → action = 😊

---

## Example Sessions

### Example 1: Quick Feature

```bash
$ rforge:plan "add print method to mediation objects"

Questions:
1. Scope? [a] One function ←
2. Users? [b] MediationVerse users ←
3. Timeline? [a] Today ←
4. Complexity? [a] Simple ←
5. Breaking changes? [a] No ←

Analysis...
✓ Similar: print.lm() (R base)
✓ Objects: 3 types (mediation, ci, sensitivity)
✓ Current: default print (ugly)
✓ Time: 1-2 hours

Option A: Basic print ⚡
- Pretty output for all object types
- Today (1-2 hours)
- Copy print.lm() pattern
→ RECOMMENDED

Option B: Fancy print with options 🔧
- Customizable (digits, width, etc.)
- 1 day
- More code, more testing
→ OVERKILL for now

Pick: [A]

Generated: RFORGE-print-methods-2025-12-20.md

Next:
1. rforge:pkg:scaffold method print.mediation
2. Copy pattern from print.lm()
3. Test with example objects
4. Done!

Ready? [Y]
```

**Result:** 5 min planning → 1 hour coding → Done! ✓

---

### Example 2: Bug Fix

```bash
$ rforge:plan:quick-fix "bootstrap CI too wide for large N"

Questions:
1. Package? [auto: RMediation] ✓
2. Severity? [b] Medium (affects results) ←
3. Fix now? [a] Yes ←

Analysis...
✓ Location: ci_mediation.R:145
✓ Issue: nboot=1000 insufficient for large N
✓ Fix: Increase nboot based on sample size
✓ Tests: test_ci_mediation.R

Approach:
1. Add adaptive nboot: n < 100 → 1000, n > 100 → 5000
2. Update documentation
3. Run tests

Time: 30 minutes

Start? [Y]
```

**Result:** 1 min planning → 30 min coding → Done! ✓

---

## Success Criteria

**A good ideation tool should:**

✅ **Fast:** Idea → spec in < 5 minutes
✅ **Clear:** 2-3 options max, not 10
✅ **Actionable:** Spec includes exact next steps
✅ **ADHD-Friendly:** Minimal decisions, quick wins highlighted
✅ **Persistent:** Everything saved, no lost context
✅ **Integrated:** Leads directly to execution tools

**It should NOT:**

❌ Ask too many questions (analysis paralysis)
❌ Generate huge documents (overwhelming)
❌ Be generic (needs to understand R package dev)
❌ Require manual spec writing (automate!)

---

## Implementation Priority

### Phase 1: Core (Week 1)
1. ⭐ `rforge:plan` - Main ideation tool
2. `rforge:plan:quick-fix` - Bug fixes

### Phase 2: Extensions (Week 2)
3. `rforge:plan:new-package` - Package creation
4. `rforge:plan:vignette` - Documentation

### Phase 3: Advanced (Week 3)
5. `rforge:plan:refactor` - Code cleanup

---

## Open Questions

1. **Spec Format:**
   - Markdown (current proposal) or interactive web view?
   - Include code templates in spec?

2. **Context Detection:**
   - How much can we auto-detect (git branch, package name, etc.)?
   - Access to codebase analysis tools?

3. **Learning:**
   - Track which options users pick?
   - Improve time estimates over time?

4. **Integration:**
   - Auto-run `rforge:pkg:scaffold` after planning?
   - Or keep planning/execution separate?

---

## Next Steps

**To implement `rforge:plan`:**

1. **Design conversation flow** (refine 5 questions)
2. **Create option templates** (Quick/Balanced/Comprehensive)
3. **Build spec generator** (Markdown formatter)
4. **Add context analysis** (similar code detection)
5. **Test with real examples** (your actual R package work)

**Status:** Design complete, ready for implementation! 🚀

Would you like to:
- A) Refine the 5 questions for `rforge:plan`?
- B) Start implementing `rforge:plan` prototype?
- C) Adjust anything in this design?
