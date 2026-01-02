#!/bin/bash
set -euo pipefail

# aiterm installer
# Terminal optimizer for AI-assisted development
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash
#
# Options:
#   INSTALL_METHOD=pip|pipx|uv|brew  (default: auto-detect)
#   AITERM_VERSION=x.y.z             (default: latest)

REPO="Data-Wise/aiterm"
PACKAGE="aiterm-dev"
BREW_TAP="data-wise/tap"
BREW_FORMULA="aiterm"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

info() { echo -e "${BLUE}==>${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; exit 1; }

# Detect best installation method
detect_install_method() {
    if [[ -n "${INSTALL_METHOD:-}" ]]; then
        echo "$INSTALL_METHOD"
        return
    fi

    # Prefer uv (fastest)
    if command -v uv &>/dev/null; then
        echo "uv"
    # Then pipx (isolated)
    elif command -v pipx &>/dev/null; then
        echo "pipx"
    # Then Homebrew (macOS)
    elif command -v brew &>/dev/null && [[ "$(uname -s)" == "Darwin" ]]; then
        echo "brew"
    # Fallback to pip
    elif command -v pip3 &>/dev/null; then
        echo "pip"
    elif command -v pip &>/dev/null; then
        echo "pip"
    else
        error "No supported package manager found. Install pip, pipx, uv, or Homebrew."
    fi
}

# Get latest version from PyPI
get_latest_version() {
    if [[ -n "${AITERM_VERSION:-}" ]]; then
        echo "$AITERM_VERSION"
        return
    fi

    curl -fsSL "https://pypi.org/pypi/${PACKAGE}/json" 2>/dev/null | \
        grep -o '"version":"[^"]*"' | head -1 | cut -d'"' -f4
}

# Install with uv
install_uv() {
    local version=$1
    info "Installing with uv (fastest)..."

    if [[ -n "$version" ]]; then
        uv tool install "${PACKAGE}==${version}"
    else
        uv tool install "$PACKAGE"
    fi
}

# Install with pipx
install_pipx() {
    local version=$1
    info "Installing with pipx (isolated environment)..."

    if [[ -n "$version" ]]; then
        pipx install "${PACKAGE}==${version}"
    else
        pipx install "$PACKAGE"
    fi
}

# Install with pip
install_pip() {
    local version=$1
    info "Installing with pip..."

    local pip_cmd="pip3"
    command -v pip3 &>/dev/null || pip_cmd="pip"

    if [[ -n "$version" ]]; then
        $pip_cmd install --user "${PACKAGE}==${version}"
    else
        $pip_cmd install --user "$PACKAGE"
    fi

    warn "Installed with --user flag. Ensure ~/.local/bin is in your PATH."
}

# Install with Homebrew
install_brew() {
    info "Installing with Homebrew..."

    # Add tap if needed
    if ! brew tap | grep -q "$BREW_TAP"; then
        info "Adding tap ${BREW_TAP}..."
        brew tap "$BREW_TAP"
    fi

    brew install "$BREW_FORMULA"
}

# Verify installation
verify_install() {
    info "Verifying installation..."

    if command -v aiterm &>/dev/null; then
        local installed_version
        installed_version=$(aiterm --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        success "aiterm v${installed_version} installed successfully!"
        echo ""
        info "Quick start:"
        echo "  aiterm doctor    # Check installation"
        echo "  aiterm detect    # Detect project context"
        echo "  aiterm --help    # See all commands"
        return 0
    elif command -v ait &>/dev/null; then
        success "aiterm installed (available as 'ait')"
        return 0
    else
        error "Installation verification failed. 'aiterm' command not found in PATH."
    fi
}

# Main installation flow
main() {
    echo ""
    echo -e "${BOLD}aiterm installer${NC}"
    echo "Terminal optimizer for AI-assisted development"
    echo ""

    local method version
    method=$(detect_install_method)
    version=$(get_latest_version)

    info "Install method: ${method}"
    [[ -n "$version" ]] && info "Version: ${version}"
    echo ""

    case "$method" in
        uv)     install_uv "$version" ;;
        pipx)   install_pipx "$version" ;;
        pip)    install_pip "$version" ;;
        brew)   install_brew ;;
        *)      error "Unknown install method: $method" ;;
    esac

    echo ""
    verify_install
}

main "$@"
