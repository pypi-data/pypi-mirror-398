#!/bin/bash
#
# EEveon CI/CD Pipeline Installer
#

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              EEveon CI/CD Pipeline Installer                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
EEVEON_CMD="$BIN_DIR/eeveon"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Please don't run this as root"
    exit 1
fi

echo "[1/5] Checking dependencies..."

# Check for required commands
MISSING_DEPS=()

if ! command -v git &> /dev/null; then
    MISSING_DEPS+=("git")
fi

if ! command -v jq &> /dev/null; then
    MISSING_DEPS+=("jq")
fi

if ! command -v rsync &> /dev/null; then
    MISSING_DEPS+=("rsync")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_DEPS+=("python3")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "❌ Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Install them with:"
    echo "  sudo apt update"
    echo "  sudo apt install -y ${MISSING_DEPS[*]}"
    echo ""
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y "${MISSING_DEPS[@]}"
    else
        echo "Please install dependencies and run again"
        exit 1
    fi
fi

echo "✅ All dependencies installed"
echo ""

echo "[2/5] Setting up directory structure..."

# Create directories
mkdir -p "$SCRIPT_DIR"/{bin,config,logs,scripts,deployments}

echo "✅ Directory structure created"
echo ""

echo "[3/5] Making scripts executable..."

chmod +x "$EEVEON_CMD"
chmod +x "$SCRIPT_DIR/scripts/"*.sh

echo "✅ Scripts are executable"
echo ""

echo "[4/5] Adding eeveon to PATH..."

# Add to PATH in .bashrc if not already there
BASHRC="$HOME/.bashrc"
PATH_LINE="export PATH=\"$BIN_DIR:\$PATH\""

if ! grep -q "EEveon CI/CD" "$BASHRC"; then
    echo "" >> "$BASHRC"
    echo "# EEveon CI/CD Pipeline" >> "$BASHRC"
    echo "$PATH_LINE" >> "$BASHRC"
    echo "✅ Added to PATH in ~/.bashrc"
else
    echo "✅ Already in PATH"
fi

echo ""

echo "[5/5] Creating initial configuration..."

# Create empty config if it doesn't exist
CONFIG_FILE="$SCRIPT_DIR/config/pipeline.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "{}" > "$CONFIG_FILE"
    echo "✅ Created configuration file"
else
    echo "✅ Configuration file exists"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete!                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Reload your shell:"
echo "   source ~/.bashrc"
echo ""
echo "2. Initialize your first pipeline:"
echo "   eeveon init --repo https://github.com/user/repo.git \\"
echo "               --name myproject \\"
echo "               --path /var/www/myproject"
echo ""
echo "3. Start monitoring:"
echo "   eeveon start myproject -f"
echo ""
echo "For help:"
echo "   eeveon --help"
echo ""
echo "Documentation:"
echo "   cat $SCRIPT_DIR/README.md"
echo ""
