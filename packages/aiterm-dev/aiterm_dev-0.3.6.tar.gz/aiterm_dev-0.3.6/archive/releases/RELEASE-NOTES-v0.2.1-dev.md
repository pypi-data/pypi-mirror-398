# Release Notes - v0.2.1-dev

**Version:** 0.2.1-dev
**Status:** Development Cycle (Not Released)
**Branch:** dev
**Started:** 2025-12-25 (immediately after v0.2.0 release)

---

## Overview

v0.2.1-dev is a maintenance and polish release focused on:
1. **PyPI Publication** - Make aiterm installable via `pip install aiterm`
2. **CI/CD Infrastructure** - GitHub Actions for automated testing and releases
3. **Documentation Polish** - Fix remaining validation issues
4. **Quality Improvements** - Dynamic badges, coverage tracking

**Target Timeline:** 1-2 weeks

---

## Planned Features

### 1. PyPI Publication 📦

**Priority:** HIGH (Primary goal for v0.2.1)

**Tasks:**
- [ ] Validate package structure for PyPI
- [ ] Create PyPI account and verify email
- [ ] Generate API token for automated publishing
- [ ] Test package upload to TestPyPI
- [ ] Publish to production PyPI
- [ ] Update installation docs with `pip install aiterm`
- [ ] Add PyPI badge to README and docs

**Why Important:**
- Makes aiterm accessible to wider Python community
- Simplifies installation (no git clone needed)
- Enables version pinning and dependency management
- Standard Python package distribution

**Installation After PyPI:**
```bash
# Current (v0.2.0)
uv tool install git+https://github.com/Data-Wise/aiterm
pipx install git+https://github.com/Data-Wise/aiterm

# After v0.2.1
pip install aiterm          # NEW!
pipx install aiterm         # Simpler!
uv tool install aiterm      # Simpler!
```

---

### 2. GitHub Actions CI/CD 🔄

**Priority:** HIGH

**Tasks:**
- [ ] Create `.github/workflows/test.yml` - Run tests on push/PR
- [ ] Create `.github/workflows/publish.yml` - Auto-publish to PyPI on release
- [ ] Set up test matrix (Python 3.10, 3.11, 3.12)
- [ ] Add macOS and Linux test runners
- [ ] Configure pytest with coverage reporting
- [ ] Set up branch protection rules

**Why Important:**
- Automated testing prevents regressions
- Catch issues before merge
- Automated releases reduce manual work
- Multi-platform testing ensures compatibility

**Workflows Planned:**
```yaml
# .github/workflows/test.yml
- Run on: push to dev/main, pull requests
- Test matrix: Python 3.10, 3.11, 3.12 on macOS + Linux
- Coverage reporting to Codecov

# .github/workflows/publish.yml
- Run on: GitHub release created
- Build package
- Publish to PyPI
- Update Homebrew tap
```

---

### 3. Codecov Integration 📊

**Priority:** MEDIUM

**Tasks:**
- [ ] Create Codecov account
- [ ] Add repository to Codecov
- [ ] Configure GitHub Actions to upload coverage
- [ ] Add coverage badge to README
- [ ] Set coverage targets (maintain 83%+)

**Why Important:**
- Track test coverage over time
- Prevent coverage regressions
- Identify untested code paths
- Professional project quality signal

---

### 4. Dynamic Badges 🏷️

**Priority:** MEDIUM

**Tasks:**
- [ ] Replace static version badge with shields.io dynamic badge
- [ ] Replace static tests badge with GitHub Actions status
- [ ] Replace static coverage badge with Codecov badge
- [ ] Update docs/index.md with dynamic badges
- [ ] Update README.md with dynamic badges

**Current (Static):**
```markdown
![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Tests](https://img.shields.io/badge/tests-29%20passed-success)
![Coverage](https://img.shields.io/badge/coverage-83%25-green)
```

**After (Dynamic):**
```markdown
![PyPI](https://img.shields.io/pypi/v/aiterm)
![Tests](https://github.com/Data-Wise/aiterm/actions/workflows/test.yml/badge.svg)
![Coverage](https://codecov.io/gh/Data-Wise/aiterm/branch/main/graph/badge.svg)
```

---

### 5. Documentation Cleanup 📚

**Priority:** LOW (Deferred from v0.2.0)

**Tasks:**
- [ ] Fix 29 code example validation warnings
- [ ] Review all code blocks for proper language tags
- [ ] Separate output examples from executable code
- [ ] Update DOCUMENTATION-CLEANUP.md as issues are fixed

**Reference:** See `DOCUMENTATION-CLEANUP.md` for full list of issues.

**Why Low Priority:**
- Non-blocking issues (warnings, not errors)
- Documentation is functional and accurate
- Can be addressed incrementally

---

### 6. Automated Release Notes 🤖

**Priority:** LOW (Nice to have)

**Tasks:**
- [ ] Create script to generate release notes from commits
- [ ] Parse conventional commits for categorization
- [ ] Auto-update CHANGELOG.md on release
- [ ] Integrate with GitHub Actions release workflow

**Why Useful:**
- Reduces manual release work
- Consistent release note format
- Automatic changelog updates

---

## Success Criteria

### Must Have (Required for v0.2.1 release)
- [x] v0.2.0 successfully released ✅
- [ ] Published to PyPI
- [ ] GitHub Actions CI/CD working
- [ ] All tests passing on CI
- [ ] Installation via `pip install aiterm` works

### Should Have (Highly desired)
- [ ] Codecov integration complete
- [ ] Dynamic badges replacing static badges
- [ ] Multi-platform testing (macOS + Linux)
- [ ] Automated PyPI publishing on release

### Nice to Have (Optional)
- [ ] 29 documentation warnings fixed
- [ ] Automated release notes generation
- [ ] Coverage increase (83% → 85%+)

---

## Known Issues to Address

### From v0.2.0

1. **Documentation Code Examples** (29 warnings)
   - Output examples mislabeled as executable code
   - Documented in DOCUMENTATION-CLEANUP.md
   - Non-critical, deferred to v0.2.1

2. **Static Badges**
   - Version, tests, coverage badges are static
   - Should be dynamic (GitHub Actions, Codecov)
   - Will be fixed in v0.2.1

### New Issues (To be discovered)
- Track new issues in GitHub Issues
- Label with `v0.2.1` milestone

---

## Development Workflow

### Branch Strategy
- **dev** - Active development branch (v0.2.1-dev)
- **main** - Stable releases only (v0.2.0)
- Feature branches for larger changes

### Testing
```bash
# Local testing
pytest                          # Run all tests
pytest --cov=aiterm            # With coverage
pytest -v tests/integration/   # Integration tests only

# Validate package
python -m build                # Build distribution
twine check dist/*             # Validate package

# Test installation
pip install -e .               # Editable install
aiterm doctor                  # Verify installation
```

### PyPI Publishing Workflow
```bash
# 1. Test on TestPyPI first
python -m build
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ aiterm

# 2. If successful, publish to PyPI
twine upload dist/*

# 3. Verify installation
pip install aiterm
aiterm --version
```

---

## Timeline Estimate

**Total Duration:** 1-2 weeks

### Week 1 (Days 1-3)
- [ ] **Day 1:** PyPI setup and TestPyPI publishing
- [ ] **Day 2:** GitHub Actions CI setup and testing
- [ ] **Day 3:** Codecov integration and badge updates

### Week 2 (Days 4-7)
- [ ] **Day 4:** Production PyPI publish and verification
- [ ] **Day 5:** Documentation polish (fix warnings)
- [ ] **Day 6:** Testing and validation
- [ ] **Day 7:** Release v0.2.1

**Accelerated Path (1 week):**
- Focus only on Must Have items
- Skip documentation cleanup
- Defer automated release notes to v0.2.2

---

## Post-Release Plans

### v0.2.2 (Future)
- Bug fixes discovered in v0.2.1
- Documentation improvements
- Community feedback integration

### v0.3.0 (Future - Major Features)
**Timeline:** TBD based on user feedback

**Potential Features:**
- Multi-terminal support (Warp, Alacritty, Kitty)
- Gemini CLI integration enhancements
- Plugin system for custom extensions
- Web UI for configuration
- MCP server creation wizard

**Decision Criteria:**
- User feedback from v0.2.x releases
- Pain points identified in real usage
- Community feature requests

---

## Resources

### PyPI Publishing
- **Official Guide:** https://packaging.python.org/tutorials/packaging-projects/
- **Twine Docs:** https://twine.readthedocs.io/
- **TestPyPI:** https://test.pypi.org/

### GitHub Actions
- **Starter Workflows:** https://github.com/actions/starter-workflows
- **Python Package:** https://docs.github.com/actions/automating-builds-and-tests/building-and-testing-python

### Codecov
- **Getting Started:** https://docs.codecov.com/docs
- **GitHub Actions:** https://github.com/codecov/codecov-action

---

## Contributing

**Development Setup:**
```bash
# Clone and setup
git clone https://github.com/Data-Wise/aiterm.git
cd aiterm
git checkout dev

# Create virtual environment
uv venv
source .venv/bin/activate

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
```

**Pull Request Process:**
1. Create feature branch from `dev`
2. Make changes with tests
3. Run full test suite
4. Submit PR to `dev` branch
5. Wait for CI to pass
6. Request review

---

## Questions & Feedback

**Have questions about v0.2.1 development?**
- GitHub Issues: https://github.com/Data-Wise/aiterm/issues
- GitHub Discussions: https://github.com/Data-Wise/aiterm/discussions
- Label: `v0.2.1`, `question`

**Want to contribute?**
- Check open issues labeled `v0.2.1`
- See `CONTRIBUTING.md` (coming soon)
- Start a discussion for new ideas

---

## Version History

- **v0.2.0** (2025-12-24) - Phase 3A Complete (4 feature systems)
- **v0.2.1-dev** (2025-12-25 - present) - PyPI & CI/CD focus
- **v0.2.1** (TBD) - Target: Early January 2026

---

**Status:** 📝 Planning Phase
**Next Step:** PyPI publication setup
**Branch:** dev (v0.2.1-dev)
