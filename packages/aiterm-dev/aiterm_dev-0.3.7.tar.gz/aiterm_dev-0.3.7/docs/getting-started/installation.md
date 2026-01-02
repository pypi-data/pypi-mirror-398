# Installation

Complete installation guide for **aiterm** v0.1.0.

---

## Requirements

### System Requirements

- **Operating System:** macOS (Linux support coming in v0.2.0)
- **Python:** 3.10 or higher
- **Terminal:** iTerm2 (other terminals coming in v0.2.0)

### Optional Requirements

- **Claude Code CLI:** For Claude Code integration features
- **Gemini CLI:** For Gemini integration (v0.2.0+)
- **Git:** For git branch/status detection

---

## Installation Methods

### Method 1: Homebrew (macOS - Recommended 🍺)

**Homebrew** is the easiest way to install aiterm on macOS. One command, automatic updates, no Python setup needed.

#### Install Homebrew (if needed)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Install aiterm

```bash
# Install from Data-Wise tap
brew install data-wise/tap/aiterm

# Verify installation
aiterm --version
ait --version  # Short alias also works
```

#### Update aiterm

```bash
# Update to latest version
brew upgrade aiterm

# Or update all Homebrew packages
brew upgrade
```

#### Uninstall

```bash
brew uninstall aiterm
```

**Why Homebrew?**

- ✅ One-line installation
- ✅ Automatic dependency management (Python, etc.)
- ✅ Simple updates with `brew upgrade`
- ✅ Standard macOS package manager
- ✅ No virtual environment configuration needed

---

### Method 2: UV (Cross-Platform ⚡)

**UV** is 10-100x faster than pip and works on all platforms.

#### Install UV

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

#### Install aiterm

```bash
# Install aiterm as a CLI tool
uv tool install git+https://github.com/Data-Wise/aiterm

# Verify installation
aiterm --version
ait --version  # Short alias also works
```

#### Update aiterm

```bash
# Update to latest version
uv tool upgrade aiterm
```

---

### Method 3: pipx

**pipx** installs Python CLI tools in isolated environments.

#### Install pipx

```bash
# Install pipx
python3 -m pip install --user pipx

# Add pipx to PATH
python3 -m pipx ensurepath

# Restart your terminal, then verify
pipx --version
```

#### Install aiterm

```bash
# Install aiterm
pipx install git+https://github.com/Data-Wise/aiterm

# Verify installation
aiterm --version
```

#### Update aiterm

```bash
# Update to latest version
pipx upgrade aiterm
```

---

### Method 4: Development Installation

For contributing or local development:

```bash
# Clone the repository
git clone https://github.com/Data-Wise/aiterm.git
cd aiterm

# Create virtual environment with uv
uv venv

# Activate environment
source .venv/bin/activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest -v

# Verify installation
aiterm --version
```

---

## Post-Installation

### Verify Installation

```bash
# Check version
aiterm --version

# Run health check
aiterm doctor

# Test context detection
aiterm detect
```

Expected output from `aiterm doctor`:

```
aiterm doctor - Health check

Terminal: iTerm.app
Shell: /bin/zsh
Python: 3.10+
aiterm: 0.1.0-dev

Basic checks passed!
```

### Shell Completion (Optional)

Enable tab completion for your shell:

#### Zsh

```bash
# Add to ~/.zshrc
eval "$(_AITERM_COMPLETE=zsh_source aiterm)"

# Reload shell
source ~/.zshrc
```

#### Bash

```bash
# Add to ~/.bashrc
eval "$(_AITERM_COMPLETE=bash_source aiterm)"

# Reload shell
source ~/.bashrc
```

---

## Troubleshooting

### Command Not Found

If `aiterm` command is not found after installation:

**UV users:**
```bash
# Check UV bin directory is in PATH
echo $PATH | grep -o ~/.local/bin

# If not found, add to your shell config (~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"
```

**pipx users:**
```bash
# Ensure pipx path
python3 -m pipx ensurepath

# Restart terminal
```

### Permission Denied

If you get permission errors:

```bash
# Don't use sudo with uv or pipx!
# They install to user directories automatically

# If you accidentally used sudo, uninstall and reinstall:
uv tool uninstall aiterm
uv tool install git+https://github.com/Data-Wise/aiterm
```

### Python Version Issues

```bash
# Check Python version
python3 --version

# aiterm requires Python 3.10+
# Update Python if needed:
brew install python@3.12  # macOS with Homebrew
```

### iTerm2 Not Detected

If `aiterm doctor` shows wrong terminal:

```bash
# Check TERM_PROGRAM environment variable
echo $TERM_PROGRAM

# Should show: iTerm.app
# If not, you're not running in iTerm2
```

---

## Installation Methods Comparison

| Method | Platform | Speed | Updates | Best For |
|--------|----------|-------|---------|----------|
| **Homebrew** 🍺 | macOS | Fast | `brew upgrade` | Mac users (recommended) |
| **UV** ⚡ | All | Fastest | `uv tool upgrade` | Cross-platform, speed |
| **pipx** | All | Fast | `pipx upgrade` | Python developers |
| **Source** | All | Slow | `git pull` | Contributors |

---

## Uninstalling

### Homebrew

```bash
brew uninstall aiterm
```

### UV

```bash
uv tool uninstall aiterm
```

### pipx

```bash
pipx uninstall aiterm
```

### Development Install

```bash
cd aiterm
uv pip uninstall aiterm
```

---

## Next Steps

- ✅ **Quick Start:** [Get started in 2 minutes](quickstart.md)
- 📖 **CLI Reference:** [All commands and examples](../reference/commands.md)
- 🎯 **Workflows:** [Common use cases](../guide/workflows.md)
- ⚙️ **Claude Integration:** [Set up auto-approvals](../guide/claude-integration.md)

---

## Version Information

- **Current Version:** 0.1.0-dev
- **Release Date:** December 2024
- **Python Support:** 3.10, 3.11, 3.12, 3.13, 3.14
- **macOS Support:** Monterey (12.0) and later

---

## Getting Help

- **Documentation:** [https://data-wise.github.io/aiterm](https://data-wise.github.io/aiterm)
- **Issues:** [GitHub Issues](https://github.com/Data-Wise/aiterm/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Data-Wise/aiterm/discussions)
