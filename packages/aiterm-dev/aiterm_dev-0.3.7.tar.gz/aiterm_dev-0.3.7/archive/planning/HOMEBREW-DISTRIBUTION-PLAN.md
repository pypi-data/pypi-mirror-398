# Homebrew Distribution Plan

**Generated:** 2025-12-21
**Project:** aiterm v0.2.0-dev
**Goal:** Professional macOS distribution via Homebrew

---

## Overview

Homebrew is the ideal primary distribution method for aiterm because:
1. Target users are Mac developers (iTerm2 requirement)
2. One-line installation (`brew install data-wise/tap/aiterm`)
3. Automatic dependency management (Python 3.10+)
4. Familiar update workflow (`brew upgrade aiterm`)
5. Professional appearance for public release

---

## Phased Rollout

### Phase 1: Private Tap Testing (Week 1) - v0.2.7

**Goal:** Validate formula works end-to-end

**Tasks:**
1. **Create Homebrew Formula** (1 hour)
   ```ruby
   # Formula/aiterm.rb in ~/homebrew-tap
   class Aiterm < Formula
     include Language::Python::Virtualenv

     desc "Terminal optimizer for AI-assisted development"
     homepage "https://github.com/Data-Wise/aiterm"
     url "https://github.com/Data-Wise/aiterm/archive/v0.2.7.tar.gz"
     sha256 "TBD"  # Computed after creating GitHub release
     license "MIT"

     depends_on "python@3.12"

     def install
       virtualenv_install_with_resources
     end

     test do
       assert_match version.to_s, shell_output("#{bin}/aiterm --version")
       system bin/"aiterm", "doctor"
     end
   end
   ```

2. **Test Locally** (30 min)
   ```bash
   cd ~/homebrew-tap
   brew install --build-from-source ./Formula/aiterm.rb
   aiterm --version
   aiterm doctor
   aiterm detect
   ```

3. **Push to Private Tap** (15 min)
   ```bash
   git add Formula/aiterm.rb
   git commit -m "feat: add aiterm formula"
   git push
   ```

4. **Test from Tap** (30 min)
   ```bash
   brew uninstall aiterm
   brew install data-wise/tap/aiterm
   aiterm --version  # Should work!
   ```

**Success Criteria:**
- Formula installs without errors
- All commands work (`doctor`, `detect`, `switch`)
- Can upgrade with `brew upgrade aiterm`
- Can uninstall cleanly

---

### Phase 2: Automated Releases (Week 2) - v0.2.7

**Goal:** Zero-touch releases via GitHub Actions

**Create `.github/workflows/release.yml`:**
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  pypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Build and publish to PyPI
        run: |
          pip install build twine
          python -m build
          twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}

  homebrew:
    needs: pypi
    runs-on: ubuntu-latest
    steps:
      - name: Update Homebrew formula
        uses: mislav/bump-homebrew-formula-action@v2
        with:
          formula-name: aiterm
          tap: Data-Wise/homebrew-tap
          download-url: https://github.com/Data-Wise/aiterm/archive/${{ github.ref_name }}.tar.gz
        env:
          COMMITTER_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}

  release-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate changelog
        uses: orhun/git-cliff-action@v2
        with:
          config: cliff.toml
          args: --latest --strip header
```

**Setup Requirements:**
1. PyPI account + API token (`PYPI_TOKEN` secret)
2. GitHub personal access token for tap repo (`HOMEBREW_TAP_TOKEN`)
3. Configure `bump2version` for version management

**Release Workflow:**
```bash
# 1. Bump version
bump2version minor  # or patch, major

# 2. Create tag
git tag v0.2.7
git push --tags

# 3. GitHub Action automatically:
#    - Builds package
#    - Uploads to PyPI
#    - Updates Homebrew formula
#    - Creates GitHub release with notes
```

**Success Criteria:**
- Tag push triggers all automation
- PyPI gets new version within 5 minutes
- Homebrew formula updates automatically
- Release notes generated from commits

---

### Phase 3: Public Release (v0.3.0)

**Goal:** Public tap, announce to community

**Tasks:**
1. **Make Tap Public**
   - Update tap repo visibility to public
   - Add README to tap explaining usage
   - Add LICENSE file

2. **Update Documentation**
   ```markdown
   ## Installation

   ### macOS (Recommended)
   ```bash
   brew tap data-wise/tap
   brew install aiterm
   ```

   ### All Platforms
   ```bash
   pip install aiterm
   # or
   uv pip install aiterm
   ```

   ### Installation Options Comparison

   | Platform | Primary Method | Alternative |
   |----------|---------------|-------------|
   | macOS | Homebrew | pip/UV |
   | Linux | pip/UV | - |
   | Windows | pip/UV | - |
   ```

3. **Add Homebrew Badge**
   ```markdown
   [![Homebrew](https://img.shields.io/badge/homebrew-data--wise%2Ftap-orange)](https://github.com/Data-Wise/homebrew-tap)
   ```

4. **Announce**
   - Tweet/post about Homebrew availability
   - Update project documentation site
   - Add to awesome-claude-code list (if exists)

**Success Criteria:**
- 10+ external users install via Homebrew
- No installation issues reported
- Positive feedback on ease of installation

---

### Phase 4: Homebrew Core (v0.5.0+)

**Goal:** Get into official Homebrew (no tap needed)

**Prerequisites:**
- [ ] 75+ GitHub stars
- [ ] 30+ days since first release
- [ ] Active maintenance (weekly commits)
- [ ] No open installation bugs
- [ ] Comprehensive documentation

**Submission Process:**
1. Review [homebrew-core guidelines](https://docs.brew.sh/Formula-Cookbook)
2. Ensure formula follows all best practices:
   - No hardcoded paths
   - Proper dependency declarations
   - Comprehensive test block
   - No unnecessary dependencies
3. Create PR to `homebrew/homebrew-core`
4. Respond to maintainer feedback
5. Maintain formula in core repo

**Timeline:**
- Earliest: 6 months after v0.1.0 release
- Realistic: 9-12 months

**Benefits:**
- Installation becomes: `brew install aiterm` (no tap!)
- Maximum discoverability
- Homebrew team validates quality
- Included in `brew search` results
- Automatic CI/CD testing by Homebrew

---

## Technical Details

### Formula Structure Explained

```ruby
class Aiterm < Formula
  # Use Python virtualenv installer
  include Language::Python::Virtualenv

  # Metadata
  desc "Terminal optimizer for AI-assisted development"
  homepage "https://github.com/Data-Wise/aiterm"
  url "https://github.com/Data-Wise/aiterm/archive/v0.2.7.tar.gz"
  sha256 "abc123..."  # Computed with: curl -L <url> | shasum -a 256
  license "MIT"

  # Dependencies (Homebrew will install these)
  depends_on "python@3.12"

  # Installation logic
  def install
    # Creates virtualenv in libexec
    # Installs package with dependencies
    # Links bin/aiterm to Homebrew bin
    virtualenv_install_with_resources
  end

  # Validation tests
  test do
    # Verify version command works
    assert_match version.to_s, shell_output("#{bin}/aiterm --version")

    # Verify core command works
    system bin/"aiterm", "doctor"
  end
end
```

### Dependency Management

**Homebrew handles:**
- Python 3.12 installation
- Virtual environment creation
- Package dependency resolution (from pyproject.toml)
- Binary linking to `/opt/homebrew/bin/aiterm`

**What you maintain:**
- `pyproject.toml` dependencies
- Version compatibility
- Python version requirement

---

## Installation Comparison

| Method | Command | Steps | Platform | Auto-Update |
|--------|---------|-------|----------|-------------|
| **Homebrew** | `brew install data-wise/tap/aiterm` | 1 | macOS | `brew upgrade` |
| **pip** | `pip install aiterm` | 1-2 | All | `pip install -U aiterm` |
| **UV** | `uv pip install aiterm` | 1-2 | All | `uv pip install -U aiterm` |
| **pipx** | `pipx install aiterm` | 1 | All | `pipx upgrade aiterm` |
| **Git** | `git clone ... && pip install -e .` | 3-4 | All | `git pull` |

**Recommendation:**
- **macOS users:** Homebrew (fastest, most familiar)
- **Linux users:** pip/UV
- **Developers:** Git clone (editable install)

---

## Testing Checklist

### Before First Release
- [ ] Create GitHub release v0.2.7
- [ ] Compute SHA256 hash
- [ ] Update formula with hash
- [ ] Test install from tarball URL
- [ ] Verify all CLI commands work
- [ ] Test upgrade path
- [ ] Test uninstall cleanup

### For Each Release
- [ ] Tag version in git
- [ ] GitHub Action completes successfully
- [ ] PyPI shows new version
- [ ] Homebrew formula updated (check tap repo)
- [ ] Test install on fresh Mac
- [ ] Verify `brew upgrade aiterm` works

### Before homebrew-core Submission
- [ ] Formula follows all best practices
- [ ] Test suite comprehensive
- [ ] Documentation complete
- [ ] No hardcoded paths
- [ ] License file present
- [ ] Changelog maintained

---

## Troubleshooting

### Common Issues

**Issue:** SHA256 mismatch
```bash
# Solution: Recompute hash
curl -L https://github.com/Data-Wise/aiterm/archive/v0.2.7.tar.gz | shasum -a 256
```

**Issue:** Python dependency conflict
```bash
# Solution: Homebrew uses isolated virtualenv (shouldn't happen)
# If it does, check pyproject.toml version pins
```

**Issue:** Command not found after install
```bash
# Solution: Check Homebrew bin is in PATH
echo $PATH | grep homebrew

# Add to .zshrc if missing:
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Issue:** Formula validation fails
```bash
# Run Homebrew audit
brew audit --strict --online Formula/aiterm.rb

# Fix reported issues
```

---

## Future Enhancements

### Multi-Version Support
```bash
# Allow installing specific versions
brew install aiterm@0.2
brew install aiterm@0.3
brew install aiterm  # Latest
```

### Standalone Binary (Alternative)
Instead of Python formula, could build standalone binary:
- Use PyInstaller or Nuitka
- Single executable (~50MB)
- No Python dependency
- Faster startup time
- Larger download size

**Trade-off:** Python formula is easier to maintain, binary is faster to install.

---

## Resources

### Documentation
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formula Guide](https://docs.brew.sh/Python-for-Formula-Authors)
- [Homebrew Core Guidelines](https://github.com/Homebrew/homebrew-core/blob/master/CONTRIBUTING.md)

### Examples
- Look at other Python CLI tools:
  ```bash
  brew cat awscli
  brew cat poetry
  brew cat pipx
  ```

### Automation
- [bump-homebrew-formula-action](https://github.com/mislav/bump-homebrew-formula-action)
- [git-cliff](https://git-cliff.org/) (changelog generation)
- [bump2version](https://github.com/c4urself/bump2version)

---

## Next Steps

1. **This Week:** Create basic formula, test in private tap
2. **Next Week:** Set up automated release workflow
3. **v0.3.0:** Public tap release + announcement
4. **v0.5.0+:** Submit to homebrew-core

**First Action:** Create GitHub release v0.2.7 to get tarball URL for testing.
