# Workflow Plugin Design - Comprehensive Brainstorm

**Generated:** 2025-12-23
**Context:** Adding brainstorm, DevOps, frontend, backend design to workflow plugin
**Goal:** Solid indie/open-source design (NOT corporate production)

---

## 📊 Research Findings

### Installed Plugins Analyzed

**From ~/.claude/plugins/cache/cc-marketplace/:**

1. **backend-architect** - API design, database optimization, authentication
2. **experienced-engineer/** - Suite of 10 specialized agents:
   - `devops-engineer` - CI/CD, IaC, containerization
   - `ux-ui-designer` - Interface design, accessibility, design systems
   - `api-architect` - REST/GraphQL API design
   - `database-architect` - Schema design, query optimization
   - `security-specialist` - Security audits, OWASP compliance
   - `performance-engineer` - Profiling, optimization
   - `testing-specialist` - Test strategies, automation
   - `tech-lead` - Architecture decisions, team coordination
   - `code-quality-reviewer` - Code reviews, best practices
   - `documentation-writer` - Technical documentation

3. **workflow-optimizer** - ADHD-friendly workflow patterns
4. **infrastructure-maintainer** - System health, scaling
5. **codebase-documenter** - CLAUDE.md generation
6. **explore** - Codebase exploration
7. **ultrathink** - Deep thinking, analysis
8. **desktop-app-dev** - Desktop application development

### Existing Workflow Commands

**Current (~5,656 lines):**
- `/recap`, `/next`, `/focus`, `/done`, `/stuck`
- `/brainstorm` (already exists! - with background delegation)
- `/refine`, `/task-*` commands
- Documentation automation (Phase 2)

---

## 🎯 Design Philosophy

### "Solid Indie Design" Principles

**What We WANT:**
- ✅ Clean, maintainable architecture
- ✅ Well-tested core functionality
- ✅ Excellent developer experience
- ✅ Fast, responsive commands
- ✅ Clear, helpful error messages
- ✅ Extensible design patterns
- ✅ Good documentation
- ✅ Thoughtful defaults

**What We DON'T WANT:**
- ❌ Over-engineered enterprise patterns
- ❌ Excessive abstraction layers
- ❌ "Resume-driven development"
- ❌ Framework for framework's sake
- ❌ Premature optimization
- ❌ Analysis paralysis
- ❌ Corporate bureaucracy
- ❌ Complexity without benefit

**Examples of "Solid Indie":**
- **Good:** Simple shell scripts that just work
- **Bad:** Elaborate plugin architecture for 3 functions
- **Good:** One well-tested approach
- **Bad:** Abstract factory singleton factory pattern
- **Good:** README with clear examples
- **Bad:** UML diagrams and architecture decision records

---

## 💡 COMPREHENSIVE IDEA GENERATION

### Category 1: Brainstorm Command Enhancement

#### Idea 1.1: Keep Existing `/brainstorm` Command ⭐
**Description:** The command already exists and is solid!

**Current features:**
- 5 brainstorming modes (features, solutions, improvements, alternatives, experiments)
- Smart background delegation (auto-detects long-running)
- Interactive mode
- Context detection
- Saves to IDEAS.md

**Enhancement opportunities:**
- Add domain-specific templates (DevOps, Frontend, Backend)
- Integrate with design patterns knowledge
- Auto-suggest based on project type

**Complexity:** Low (already exists!)

---

#### Idea 1.2: Add Design-Specific Brainstorm Modes
**Description:** Extend existing modes with design-focused options

**New modes:**
```
| Mode | Use For | Example |
|------|---------|---------|
| `architecture` | System design | "Design microservices architecture" |
| `frontend-ui` | UI/UX design | "Design admin dashboard" |
| `backend-api` | API design | "Design user management API" |
| `devops` | Infrastructure | "Design CI/CD pipeline" |
| `database` | Data modeling | "Design schema for multi-tenancy" |
```

**Implementation:**
```markdown
# /brainstorm --mode=backend-api "user management"

Detected: Backend API design
Analyzing patterns from:
- REST best practices
- Authentication flows
- CRUD operations
- Error handling

Generating ideas...
```

**Pros:**
- ✅ Builds on existing command
- ✅ Domain-specific guidance
- ✅ Leverages knowledge from installed plugins

**Cons:**
- ❌ More modes = more complexity
- ❌ Need to maintain design patterns knowledge

**Complexity:** Medium

---

#### ⭐ Idea 1.3: Smart Template Detection (RECOMMENDED)
**Description:** Auto-detect what kind of brainstorming based on keywords

**User says:** `/brainstorm "design user authentication API"`

**System detects:**
- Keywords: "design", "authentication", "API"
- Context: Python/Node project
- Recommendation: backend-api + security patterns

**Output:**
```
💡 Detected: Backend API Design (Authentication)

Relevant patterns:
• OAuth2 / JWT best practices
• Password hashing (bcrypt/argon2)
• Rate limiting
• Session management

Brainstorming...
```

**Why recommended:** Natural language, no need to remember modes

**Complexity:** Medium

---

### Category 2: DevOps Integration

#### Idea 2.1: `/devops` Command Suite
**Description:** DevOps-specific workflow commands

**Commands:**
```
/devops:init      - Initialize DevOps setup (CI/CD, Docker, etc.)
/devops:pipeline  - Design CI/CD pipeline
/devops:deploy    - Plan deployment strategy
/devops:monitor   - Set up monitoring/logging
/devops:security  - Security scanning setup
```

**Example workflow:**
```
User: /devops:pipeline

PIPELINE DESIGN WIZARD
────────────────────────────────────────────
Detected: Python project (pyproject.toml)

Recommended pipeline stages:
1. ✓ Lint & Format (ruff, black)
2. ✓ Type Check (mypy)
3. ✓ Unit Tests (pytest)
4. ✓ Integration Tests
5. ✓ Build (uv build)
6. ✓ Security Scan (safety, bandit)
7. ✓ Deploy to PyPI

Create GitHub Actions workflow? (y/n)
```

**Pros:**
- ✅ Guided DevOps setup
- ✅ Best practices built-in
- ✅ Project-aware

**Cons:**
- ❌ Many new commands
- ❌ Platform-specific (GitHub Actions)

**Complexity:** High

---

#### ⭐ Idea 2.2: DevOps Skill (Auto-Activating) - RECOMMENDED
**Description:** Auto-activating skill that helps with DevOps tasks

**Structure:**
```
skills/devops-consultant.md

Activates when:
- Keywords: "CI/CD", "deploy", "docker", "kubernetes"
- Files: Dockerfile, .github/workflows/, docker-compose.yml
- Questions: "How do I deploy?", "Set up pipeline"

Provides:
- CI/CD pipeline templates
- Deployment best practices
- Container optimization
- Security recommendations
```

**Why recommended:**
- ✅ Non-invasive (no new commands)
- ✅ Just works when needed
- ✅ ADHD-friendly (less to remember)

**Complexity:** Low-Medium

---

#### Idea 2.3: CI/CD Template Generator
**Description:** Interactive generator for common CI/CD setups

**Supported platforms:**
- GitHub Actions
- GitLab CI
- CircleCI
- Simple Makefile approach

**Interaction:**
```
/devops:pipeline

What CI/CD platform?
1. GitHub Actions (recommended)
2. GitLab CI
3. CircleCI
4. Simple Makefile

> 1

Project type: Python (detected)

Pipeline components:
☑ Lint (ruff)
☑ Format check (black)
☑ Type check (mypy)
☑ Tests (pytest)
☑ Coverage (>80%)
☑ Build
☐ Deploy to PyPI
☐ Docker build

[Space to toggle, Enter to generate]
```

**Pros:**
- ✅ Interactive, easy
- ✅ Project-aware
- ✅ Multiple platforms

**Cons:**
- ❌ Maintenance burden
- ❌ Platform-specific knowledge

**Complexity:** High

---

### Category 3: Frontend Design

#### Idea 3.1: `/frontend` Command Suite
**Description:** Frontend design and development helpers

**Commands:**
```
/frontend:design    - Design UI component
/frontend:a11y      - Accessibility audit
/frontend:layout    - Responsive layout design
/frontend:theme     - Design system/theme
/frontend:forms     - Form design with validation
```

**Example:**
```
/frontend:design "user profile card"

COMPONENT DESIGN
────────────────────────────────────────────
Designing: User Profile Card

Component structure:
- Avatar (responsive sizing)
- Name & role
- Bio text (truncated)
- Action buttons (primary/secondary)
- Stats section (followers, posts)

Accessibility:
☑ ARIA labels
☑ Keyboard navigation
☑ Screen reader text
☑ Color contrast (4.5:1)

Framework detected: React
Generate component code? (y/n)
```

**Pros:**
- ✅ Guided UI design
- ✅ Accessibility built-in
- ✅ Framework-aware

**Cons:**
- ❌ Many commands
- ❌ Framework-specific

**Complexity:** High

---

#### ⭐ Idea 3.2: Frontend Design Skill (Auto-Activating) - RECOMMENDED
**Description:** Like UX/UI designer from experienced-engineer plugin

**Structure:**
```
skills/frontend-designer.md

Activates when:
- Keywords: "UI", "component", "layout", "responsive", "accessibility"
- Files: *.jsx, *.vue, *.svelte, *.tsx
- Questions: "How should I design...?", "Make accessible"

Provides:
- Component design patterns
- Accessibility guidelines
- Responsive design tips
- CSS best practices
- Framework-specific advice
```

**Why recommended:**
- ✅ Non-invasive
- ✅ Context-aware
- ✅ Works with any framework

**Complexity:** Low-Medium

---

#### Idea 3.3: Design System Starter
**Description:** Generate design system boilerplate

**Generates:**
- Color palette
- Typography scale
- Spacing system
- Component library structure
- Documentation site

**Example:**
```
/frontend:design-system

DESIGN SYSTEM GENERATOR
────────────────────────────────────────────
Project: aiterm

1. Color palette
   Primary: #2563eb (blue)
   Generated:
   - blue-50 to blue-900
   - gray scale
   - semantic colors (success, error, warning)

2. Typography
   Font family: Inter (suggested)
   Scale: 1.25 (Major Third)
   - text-xs to text-5xl

3. Spacing
   Base: 0.25rem (4px)
   Scale: 4, 8, 12, 16, 24, 32, 48, 64px

4. Components
   Directory: src/components/ui/
   Initial: Button, Input, Card

Generate? (y/n)
```

**Pros:**
- ✅ Quick start for UI
- ✅ Consistent system
- ✅ Best practices

**Cons:**
- ❌ Opinionated choices
- ❌ May not fit all projects

**Complexity:** Medium-High

---

### Category 4: Backend Design

#### Idea 4.1: `/backend` Command Suite
**Description:** Backend architecture and API design

**Commands:**
```
/backend:api       - Design REST/GraphQL API
/backend:db        - Database schema design
/backend:auth      - Authentication/authorization design
/backend:cache     - Caching strategy
/backend:queue     - Background job design
```

**Example:**
```
/backend:api "user management"

API DESIGN
────────────────────────────────────────────
Designing: User Management API

Detected patterns:
- CRUD operations needed
- Authentication required
- Pagination for list endpoints

Suggested endpoints:

POST   /api/v1/users           Create user
GET    /api/v1/users           List users (paginated)
GET    /api/v1/users/:id       Get user by ID
PATCH  /api/v1/users/:id       Update user
DELETE /api/v1/users/:id       Delete user

POST   /api/v1/auth/login      Login
POST   /api/v1/auth/logout     Logout
POST   /api/v1/auth/refresh    Refresh token

Security considerations:
☑ JWT authentication
☑ Rate limiting
☑ Input validation
☑ HTTPS only
☑ CORS configuration

Generate OpenAPI spec? (y/n)
```

**Pros:**
- ✅ Structured API design
- ✅ Security built-in
- ✅ Standards-based

**Cons:**
- ❌ REST/GraphQL choice
- ❌ Many commands

**Complexity:** High

---

#### ⭐ Idea 4.2: Backend Design Skill (Auto-Activating) - RECOMMENDED
**Description:** Like backend-architect from marketplace

**Structure:**
```
skills/backend-architect.md

Activates when:
- Keywords: "API", "database", "authentication", "backend", "server"
- Files: routes/, models/, controllers/
- Questions: "How to design API?", "Database schema?"

Provides:
- API design patterns (REST, GraphQL)
- Database schema suggestions
- Authentication flows
- Caching strategies
- Error handling patterns
```

**Why recommended:**
- ✅ Non-invasive
- ✅ Covers common patterns
- ✅ Works when needed

**Complexity:** Low-Medium

---

#### Idea 4.3: Database Schema Designer
**Description:** Interactive database schema design

**Features:**
- Entity relationship design
- Migration generation
- Index suggestions
- Query optimization tips

**Example:**
```
/backend:db "blog platform"

DATABASE SCHEMA DESIGN
────────────────────────────────────────────
Designing: Blog Platform

Entities detected:
• users
• posts
• comments
• tags

users
  id (uuid, pk)
  email (varchar, unique, indexed)
  password_hash (varchar)
  created_at (timestamp)

posts
  id (uuid, pk)
  user_id (uuid, fk → users.id)
  title (varchar)
  content (text)
  published (boolean, indexed)
  created_at (timestamp, indexed)

Relationships:
- users → posts (one-to-many)
- posts → comments (one-to-many)
- posts ↔ tags (many-to-many)

Generate migration? (Alembic/Prisma/Django)
```

**Pros:**
- ✅ Visual design
- ✅ Best practices (indexes, types)
- ✅ Migration generation

**Cons:**
- ❌ ORM-specific
- ❌ Complex implementation

**Complexity:** High

---

### Category 5: Design Pattern Integration

#### Idea 5.1: Pattern Library Skills
**Description:** Auto-activating skills for common design patterns

**Skills:**
```
skills/design-patterns/
├── api-patterns.md       - REST, GraphQL, gRPC patterns
├── auth-patterns.md      - OAuth, JWT, session patterns
├── cache-patterns.md     - Cache-aside, write-through, etc.
├── database-patterns.md  - Repository, active record, etc.
├── frontend-patterns.md  - Component patterns, state management
└── devops-patterns.md    - Blue-green, canary, rolling
```

**Each skill:**
- Activates on relevant keywords
- Provides pattern examples
- Suggests trade-offs
- Links to documentation

**Pros:**
- ✅ Knowledge base built-in
- ✅ Auto-activates when relevant
- ✅ Educational

**Cons:**
- ❌ Many skills to maintain
- ❌ Risk of over-suggesting

**Complexity:** Medium-High

---

#### ⭐ Idea 5.2: Smart Pattern Suggestions (RECOMMENDED)
**Description:** Single skill that suggests patterns based on context

**Structure:**
```
skills/design-consultant.md

Activates when:
- User asks "how to design..."
- User asks "best practice for..."
- User asks "what pattern for..."

Suggests:
- Analyzes context (project type, files)
- Recommends 2-3 relevant patterns
- Explains trade-offs
- Provides code examples
```

**Example:**
```
User: "How should I handle authentication?"

Design Consultant activates:

📐 Authentication Pattern Recommendations

Based on your project (Python API):

1. ⭐ JWT with Refresh Tokens (Recommended)
   Pros: Stateless, scalable, mobile-friendly
   Cons: Token invalidation complexity
   Best for: API-first apps, microservices

2. Session-Based Authentication
   Pros: Simple, server-controlled, revocable
   Cons: Requires state, session store
   Best for: Monolithic apps, traditional web

3. OAuth2 + Social Login
   Pros: User convenience, no password management
   Cons: External dependency, complex setup
   Best for: Consumer apps, social features

Would you like code examples for any of these?
```

**Why recommended:**
- ✅ Provides guidance without overwhelming
- ✅ Educational
- ✅ Context-aware
- ✅ ADHD-friendly (clear choices)

**Complexity:** Medium

---

### Category 6: Indie-Friendly Architecture

#### Idea 6.1: "Good Enough" Architecture Patterns
**Description:** Anti-overengineering skill

**Philosophy:**
```
"Don't build for scale you don't have"
"Choose boring technology"
"Optimize for developer happiness"
"Ship early, refactor when needed"
```

**Provides:**
- When NOT to use microservices
- When SQLite is enough
- When to skip caching
- When "just use Postgres" is the answer

**Example:**
```
User: "Should I use microservices?"

Good Enough Architect activates:

🎯 Microservices Reality Check

Current project: aiterm (Python CLI)
Users: <100 (estimated)
Team size: 1 developer

Recommendation: ❌ NO, don't use microservices

Why:
• Microservices solve team/scale problems you don't have
• Adds complexity: networking, deployment, monitoring
• Harder to debug and develop locally
• Over-engineering for current needs

Better alternatives:
✅ Modular monolith (separate modules, one deployment)
✅ Clean architecture (layers within single app)
✅ Plugin system (if extensibility needed)

You can always split later when you have:
• 10+ developers
• Clear service boundaries
• Actual scaling needs
```

**Pros:**
- ✅ Fights over-engineering
- ✅ Pragmatic advice
- ✅ Saves time/complexity

**Cons:**
- ❌ May seem "unprofessional"
- ❌ Opinionated

**Complexity:** Low-Medium

---

#### ⭐ Idea 6.2: Indie Stack Recommendations (RECOMMENDED)
**Description:** Curated tech stack for indie/OSS projects

**Recommendations by domain:**

**Backend (Python):**
- FastAPI (modern, fast, type-safe)
- SQLite → Postgres (when needed)
- Pydantic (validation)
- pytest (testing)

**Backend (Node):**
- Express/Fastify (proven, simple)
- Postgres with Drizzle ORM
- Vitest (testing)

**Frontend:**
- React/Svelte (pick one, stick with it)
- Tailwind CSS (utility-first)
- shadcn/ui (component library)

**DevOps:**
- GitHub Actions (free for OSS)
- Docker (containers)
- Fly.io / Railway (simple deploy)

**Database:**
- Start: SQLite
- Scale: Postgres
- Skip: MongoDB unless document DB needed

**Pros:**
- ✅ Curated, proven choices
- ✅ Indie-friendly (cost, simplicity)
- ✅ Reduces decision fatigue

**Cons:**
- ❌ Opinionated
- ❌ May not fit all projects

**Complexity:** Low

---

### Category 7: ADHD-Friendly Design Workflows

#### Idea 7.1: Design Decision Journal
**Description:** Auto-capture design decisions

**Flow:**
```
User makes design choice → Capture WHY

Example:
User: "I'm going with JWT for auth"

System:
📝 Document Design Decision

Decision: JWT authentication
Alternatives considered: Sessions, OAuth
Reason: Stateless, good for API

Save to DESIGN-DECISIONS.md? (y/n)

File structure:
────────────────────────────────────────────
# Design Decisions

## Authentication (2025-12-23)
**Decision:** JWT with refresh tokens
**Alternatives:** Session-based, OAuth2
**Reason:** API-first architecture, mobile app planned
**Trade-offs:** Token invalidation complexity accepted
**Revisit if:** Need immediate revocation
```

**Pros:**
- ✅ Captures context
- ✅ Future reference
- ✅ ADHD-friendly (don't forget WHY)

**Cons:**
- ❌ Manual intervention
- ❌ Can become documentation burden

**Complexity:** Low-Medium

---

#### ⭐ Idea 7.2: Design Workflow Integration (RECOMMENDED)
**Description:** Integrate design patterns into existing workflow

**New workflow additions:**
```
/recap      - Include recent design decisions
/next       - Suggest design tasks (schema, API, UI)
/focus      - Design-specific focus modes
/done       - Prompt for design documentation
/brainstorm - Already handles design modes! ✅
```

**Example `/done` enhancement:**
```
Session Summary
────────────────────────────────────────────
✅ Completed:
   • Designed user authentication API
   • Created database schema

📐 Design Decisions Made:
   • JWT authentication (vs sessions)
   • Postgres (vs MongoDB)

❓ Document these decisions? (y/n)
> y

Updating DESIGN-DECISIONS.md...
✓ Saved

Commit message suggestion:
"feat: design user auth API with JWT

Design decisions:
- JWT for stateless auth
- Postgres for relational data

See DESIGN-DECISIONS.md for details"

Create commit? (y/n)
```

**Why recommended:**
- ✅ Integrates with existing workflow
- ✅ Captures context naturally
- ✅ Minimal new commands

**Complexity:** Medium

---

## 🎨 DESIGN PERSPECTIVES

### Technical Perspective: Solid Indie Architecture

**Core Principles:**
1. **KISS (Keep It Simple, Stupid)**
   - Prefer simple solutions
   - Avoid premature abstraction
   - Code should be boring

2. **YAGNI (You Aren't Gonna Need It)**
   - Build for current needs
   - Add features when needed
   - Resist future-proofing

3. **Composition over Configuration**
   - Small, focused skills
   - Combine as needed
   - No complex config files

4. **Convention over Configuration**
   - Smart defaults
   - Zero-config when possible
   - Escape hatches for power users

**Technical Decisions:**

```
✅ YES:
- Auto-activating skills (low friction)
- Markdown-based commands (simple)
- Shell scripts for system tasks (proven)
- JSON for minimal config (standard)
- Git for versioning (universal)

❌ NO:
- Custom DSL (over-engineering)
- Database for state (too heavy)
- Complex plugin system (YAGNI)
- Abstract factories (over-abstraction)
- Microservices (wrong scale)
```

---

### ADHD-Friendly Perspective

**Critical Requirements:**

1. **Reduce Decisions**
   - Auto-detect when possible
   - Suggest defaults
   - Provide 2-3 options max

2. **Immediate Feedback**
   - Fast commands (< 1s ideal)
   - Background for long tasks
   - Progress indicators

3. **Context Preservation**
   - Save design decisions
   - Document WHY
   - Easy to resume

4. **Permission to Iterate**
   - "Good enough" is OK
   - Can refactor later
   - No perfectionism

**Design Patterns:**
```
Good: /brainstorm "auth design"
  → Auto-detects backend context
  → Suggests 3 patterns
  → Explains trade-offs
  → User picks one
  → Saves decision

Bad: /brainstorm --mode=backend-api --pattern=jwt --verbose --save-to=DECISIONS.md
  → Too many options
  → Decision paralysis
  → Easy to forget syntax
```

---

### Maintenance Perspective

**Sustainability Principles:**

1. **Minimal Dependencies**
   - Use built-in tools (git, shell)
   - Avoid npm packages when possible
   - Reduce version conflicts

2. **Clear Documentation**
   - Every skill has examples
   - ADHD-friendly format
   - Explain WHY, not just HOW

3. **Automated Testing**
   - Test core workflows
   - Integration tests
   - Keep tests simple

4. **Versioning Strategy**
   - Semantic versioning
   - Changelog maintenance
   - Backward compatibility

**Avoid:**
- Complex build processes
- Fragile integrations
- Implicit dependencies
- Magic that breaks

---

## 🏆 TOP 3 RECOMMENDED APPROACHES

### ⭐ #1: Skills-Based Design (RECOMMENDED)

**What:** Auto-activating skills for DevOps, Frontend, Backend

**Structure:**
```
workflow-optimizer/
├── commands/
│   └── brainstorm.md (enhanced with design modes)
├── skills/
│   ├── devops-consultant.md
│   ├── frontend-designer.md
│   ├── backend-architect.md
│   ├── design-consultant.md (pattern suggestions)
│   └── indie-architect.md (anti-overengineering)
└── docs/
```

**Why this wins:**
- ✅ Minimal new commands (keep `/brainstorm`)
- ✅ Non-invasive (skills auto-activate)
- ✅ ADHD-friendly (less to remember)
- ✅ Easy to maintain
- ✅ Extensible (add skills as needed)

**User experience:**
```
User: "How should I design the authentication API?"

→ backend-architect skill activates
→ Suggests JWT, sessions, OAuth
→ Explains trade-offs
→ User picks one

User: "Don't overcomplicate this"

→ indie-architect skill activates
→ "Good enough" recommendations
→ Prevents over-engineering
```

**First steps:**
1. Create 5 core skills (1 day)
2. Test activation triggers (2 hours)
3. Document each skill (2 hours)
4. Integration test (1 hour)

**Complexity:** Medium
**Timeline:** 2-3 days

---

### ⭐ #2: Enhanced Brainstorm + Design Workflow

**What:** Extend existing `/brainstorm` + integrate with workflow

**Enhancements:**
1. **Smart mode detection** - Auto-detect design domain
2. **Design decision capture** - Save WHY in `/done`
3. **Pattern library** - Built-in pattern knowledge
4. **Integration** - Works with `/recap`, `/next`, `/focus`

**Structure:**
```
commands/
├── brainstorm.md (enhanced)
│   ├── Auto-detect design domain
│   ├── Suggest patterns
│   └── Save decisions
└── done.md (enhanced)
    └── Capture design decisions

skills/
└── design-patterns.md (pattern library)
```

**User experience:**
```
/brainstorm "user authentication"

💡 Detected: Backend API + Security

Relevant patterns:
1. JWT Authentication
2. Session-Based Auth
3. OAuth2 Flow

Generating ideas for each approach...

[Later...]

/done

✅ Completed: Auth design

📐 Design Decision: JWT chosen
   Reason: API-first architecture

   Document this? (y/n) > y
   Saved to DESIGN-DECISIONS.md ✓
```

**Why this wins:**
- ✅ Builds on existing command
- ✅ Natural workflow integration
- ✅ Captures decisions automatically
- ✅ Minimal new concepts

**First steps:**
1. Enhance `/brainstorm` detection (1 day)
2. Add design decision capture to `/done` (1 day)
3. Create pattern library (2 days)
4. Test workflow (1 day)

**Complexity:** Medium-High
**Timeline:** 4-5 days

---

### ⭐ #3: Minimal + Focused (SHIP FAST)

**What:** Just add 3 essential skills, enhance `/brainstorm`

**Core additions:**
```
skills/
├── backend-designer.md    - API, database, auth patterns
├── frontend-designer.md   - UI, components, accessibility
└── devops-helper.md       - CI/CD, deployment, containers

commands/
└── brainstorm.md          - Add design mode detection
```

**That's it!** Keep it simple.

**Why this wins:**
- ✅ Fastest to ship (2 days)
- ✅ Covers 80% of needs
- ✅ Easy to maintain
- ✅ Room to grow

**User experience:**
```
User: "Design login API"

→ backend-designer skill activates
→ Suggests REST endpoints, auth flow
→ User implements

User: "How to deploy this?"

→ devops-helper skill activates
→ Suggests GitHub Actions + Docker
→ User sets up CI/CD
```

**First steps:**
1. Create 3 skills (1 day)
2. Enhance `/brainstorm` (4 hours)
3. Test (2 hours)
4. Ship!

**Complexity:** Low-Medium
**Timeline:** 1.5 days

---

## 🔄 HYBRID SOLUTIONS

### Combination A: #3 + #1 (Start Minimal, Add Skills)

**Phase 1:** Ship #3 (3 core skills)
**Phase 2:** Add more skills from #1 as needed

**Benefits:**
- Fast initial ship
- Iterate based on usage
- Add complexity only when valuable

---

### Combination B: #3 + Enhanced `/done`

**Add to #3:** Design decision capture in `/done`

**Why:** Captures decisions without new commands

**Extra time:** +4 hours

---

## 📊 COMPARISON MATRIX

| Approach | ADHD Score | Complexity | Ship Time | Maintenance | Extensibility |
|----------|------------|------------|-----------|-------------|---------------|
| #1 Skills | 10/10 | Medium | 2-3 days | Low | High |
| #2 Enhanced | 9/10 | Medium-High | 4-5 days | Medium | Medium |
| #3 Minimal | 10/10 | Low | 1.5 days | Low | High |
| Hybrid A | 10/10 | Low→Med | 1.5 days → grow | Low | High |

**Legend:**
- **ADHD Score:** How ADHD-friendly (10 = best)
- **Ship Time:** Time to first working version
- **Maintenance:** Ongoing effort to maintain
- **Extensibility:** Ability to add features later

---

## 💎 QUICK WINS (Do First)

### This Week

1. **Enhance `/brainstorm` with design detection** (4 hours)
   - Add keyword detection (API, UI, DevOps, DB)
   - Suggest relevant patterns
   - Test with real queries

2. **Create backend-designer skill** (3 hours)
   - API design patterns
   - Database patterns
   - Auth patterns
   - Test activation

3. **Create frontend-designer skill** (3 hours)
   - Component patterns
   - Accessibility guidelines
   - Responsive design
   - Test activation

4. **Create devops-helper skill** (3 hours)
   - CI/CD templates
   - Deployment strategies
   - Container best practices
   - Test activation

5. **Add design decision capture to `/done`** (4 hours)
   - Detect design work in session
   - Prompt to document
   - Save to DESIGN-DECISIONS.md
   - Test workflow

**Total:** ~17 hours = 2-3 days

**Result:** Core design workflow ready!

---

## 🚧 CONSTRAINTS & TRADE-OFFS

### Constraint 1: Avoid Over-Engineering
**Issue:** Easy to add too many features
**Solution:** Stick to skills (auto-activate), avoid new commands
**Trade-off:** Less explicit control, more "magic"

### Constraint 2: Pattern Knowledge Maintenance
**Issue:** Design patterns evolve
**Solution:** Focus on timeless patterns, link to external docs
**Trade-off:** May not have latest framework-specific advice

### Constraint 3: Framework Diversity
**Issue:** Can't support all frameworks
**Solution:** General patterns + framework-agnostic advice
**Trade-off:** Less specific guidance

### Constraint 4: Skill Activation Precision
**Issue:** Skills may activate unnecessarily
**Solution:** Narrow activation keywords, test thoroughly
**Trade-off:** May miss some activation opportunities

---

## 📝 DOCUMENTATION PLAN

### User Documentation

1. **DESIGN-WORKFLOWS.md** (New)
   - Using `/brainstorm` for design
   - Backend design patterns
   - Frontend design patterns
   - DevOps workflows
   - Capturing decisions

2. **PATTERN-LIBRARY.md** (New)
   - API patterns
   - Database patterns
   - Auth patterns
   - UI patterns
   - Deployment patterns

3. **Update QUICK-START.md**
   - Add design workflow example
   - Show skill activation

4. **Update REFCARD.md**
   - Add design patterns quick ref

### Developer Documentation

1. **SKILLS.md**
   - How skills work
   - Activation triggers
   - Adding new skills

---

## 🎯 FINAL RECOMMENDATION

**GO WITH: Hybrid A (#3 Minimal → #1 Skills)**

**Phase 1 (This Week):** Ship #3 Minimal
- 3 core skills (backend, frontend, devops)
- Enhanced `/brainstorm`
- Design decision capture in `/done`

**Phase 2 (Next Week):** Add from #1 as needed
- Pattern library skill
- Indie architect skill
- Additional domain skills

**Rationale:**
1. ✅ Ships fast (2 days)
2. ✅ Validates approach
3. ✅ ADHD-friendly (skills auto-activate)
4. ✅ Room to grow
5. ✅ Low maintenance
6. ✅ Solid indie design (not over-engineered)

---

## 🚀 IMMEDIATE NEXT STEPS

### Day 1 (Today)

**Morning:**
1. Create `skills/backend-designer.md` (2 hours)
   - API patterns (REST, GraphQL)
   - Database patterns
   - Auth patterns
   - Test activation

2. Enhance `/brainstorm` with detection (2 hours)
   - Add keyword matching
   - Suggest domain
   - Test queries

**Afternoon:**
3. Create `skills/frontend-designer.md` (2 hours)
   - Component patterns
   - Accessibility
   - Responsive design

4. Create `skills/devops-helper.md` (2 hours)
   - CI/CD patterns
   - Deployment strategies
   - Container advice

### Day 2 (Tomorrow)

**Morning:**
1. Add design decision capture to `/done` (3 hours)
   - Detect design work
   - Prompt for documentation
   - Save to DESIGN-DECISIONS.md

2. Integration testing (2 hours)
   - Test all skills activate correctly
   - Test `/brainstorm` detection
   - Test `/done` capture

**Afternoon:**
3. Documentation (2 hours)
   - Write DESIGN-WORKFLOWS.md
   - Update QUICK-START.md
   - Update REFCARD.md

4. Ship v0.2.0 (1 hour)
   - Test install
   - Create release
   - Update changelog

---

## 💡 KEY INSIGHTS

### Insight 1: Skills Over Commands
**Why:** Auto-activation reduces cognitive load (ADHD-friendly)
**Apply:** Create skills that just work, not commands to remember

### Insight 2: Enhance Existing, Don't Replace
**Why:** `/brainstorm` already works, build on it
**Apply:** Smart detection, not new modes

### Insight 3: "Good Enough" is a Feature
**Why:** Prevents over-engineering (indie-friendly)
**Apply:** `indie-architect` skill fights complexity

### Insight 4: Capture Context Automatically
**Why:** Design decisions get forgotten
**Apply:** `/done` prompts for documentation

### Insight 5: Keep It Boring
**Why:** Boring tech is maintainable
**Apply:** Markdown + shell scripts, not custom DSL

---

## 🎊 SUCCESS METRICS

### User Success
- ✅ Uses `/brainstorm` for design work
- ✅ Skills activate when needed
- ✅ Design decisions documented
- ✅ Feels more confident in design choices
- ✅ Doesn't feel overwhelmed

### Technical Success
- ✅ 3 skills working (backend, frontend, devops)
- ✅ Enhanced `/brainstorm` detection
- ✅ Design decision capture in `/done`
- ✅ All tests pass
- ✅ Documentation complete

### Indie Success
- ✅ Simple architecture (no over-engineering)
- ✅ Easy to maintain
- ✅ Fast commands (< 1s)
- ✅ Good developer experience
- ✅ Extensible for future

---

**Generated:** 2025-12-23
**Status:** Ready for implementation
**Next Action:** Create `skills/backend-designer.md`
**Timeline:** 2 days to ship!

---

