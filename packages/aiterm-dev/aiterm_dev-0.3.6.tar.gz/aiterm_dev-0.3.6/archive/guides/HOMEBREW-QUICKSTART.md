# Homebrew Distribution - Quick Start

**TL;DR:** Add Homebrew as primary installation method for macOS users.

---

## Why Homebrew?

✅ **Perfect fit for aiterm:**
- macOS-focused (iTerm2 requirement)
- One command: `brew install data-wise/tap/aiterm`
- Auto-updates: `brew upgrade aiterm`
- Professional distribution method

---

## 3-Step Implementation

### Step 1: Create Formula (1 hour)

Create `Formula/aiterm.rb` in your `homebrew-tap` repo:

```ruby
class Aiterm < Formula
  include Language::Python::Virtualenv

  desc "Terminal optimizer for AI-assisted development"
  homepage "https://github.com/Data-Wise/aiterm"
  url "https://github.com/Data-Wise/aiterm/archive/v0.2.7.tar.gz"
  sha256 "TBD"  # Get with: curl -L <url> | shasum -a 256
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

### Step 2: Test Locally (30 min)

```bash
cd ~/homebrew-tap
brew install --build-from-source ./Formula/aiterm.rb
aiterm --version  # Should work!
```

### Step 3: Push & Use (15 min)

```bash
git add Formula/aiterm.rb
git commit -m "feat: add aiterm formula"
git push

# Test from tap
brew uninstall aiterm
brew install data-wise/tap/aiterm
```

---

## Future: Automated Releases (Week 2)

Add `.github/workflows/release.yml` so:

```bash
git tag v0.2.7
git push --tags

# GitHub Action automatically:
# 1. Uploads to PyPI
# 2. Updates Homebrew formula
# 3. Generates release notes
```

**Setup needed:**
- PyPI API token
- GitHub token for tap repo

---

## Timeline

| Phase | When | What |
|-------|------|------|
| **Private Testing** | This week | Formula in private tap |
| **Automation** | Next week | GitHub Actions release |
| **Public Release** | v0.3.0 | Public tap + announcement |
| **Homebrew Core** | v0.5.0+ | Official `brew install aiterm` |

---

## Documentation Updates

Update README.md installation section:

```markdown
## Installation

### macOS (Recommended)
```bash
brew install data-wise/tap/aiterm
```

### All Platforms
```bash
pip install aiterm
```
```

---

## Full Details

See `HOMEBREW-DISTRIBUTION-PLAN.md` for comprehensive guide.

---

## Next Action

Create GitHub release v0.2.7 to get tarball URL for testing the formula.
