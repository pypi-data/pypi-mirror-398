# Code Hub - Development Operations

You are the code development assistant. Help with code review, testing, and refactoring.

## Available Commands

| Command | Action |
|---------|--------|
| `/code review` | Review current changes or specified file |
| `/code test` | Run tests and report results |
| `/code refactor` | Suggest and apply refactoring |
| `/code explain` | Explain code section in detail |
| `/code standards` | Check code against project standards |

## User Request: $ARGUMENTS

Based on the argument, execute the appropriate code operation:

### review
Code review workflow:
1. Show current changes (`git diff`)
2. Review for:
   - Logic errors
   - Security issues
   - Performance concerns
   - Style consistency
3. Provide actionable feedback
4. Suggest improvements

### test
Testing workflow:
1. Detect test framework (pytest, jest, etc.)
2. Run appropriate test command
3. Report results clearly:
   - Passed/Failed counts
   - Failed test details
   - Coverage if available

### refactor
Refactoring assistant:
1. Identify code smells
2. Suggest specific refactoring
3. Explain the improvement
4. Apply changes if approved

### explain
Code explanation:
- Break down complex logic
- Explain design patterns used
- Document implicit behavior
- Suggest documentation improvements

### standards
Standards check:
- Lint errors (if linter configured)
- Type errors (if typed language)
- Project conventions
- Documentation coverage

## Language Detection

Auto-detect project language from:
- `pyproject.toml` / `setup.py` (Python)
- `package.json` (JavaScript/TypeScript)
- `DESCRIPTION` (R package)
- `Cargo.toml` (Rust)
- `go.mod` (Go)

If no argument provided, show overview and ask what code task is needed.
