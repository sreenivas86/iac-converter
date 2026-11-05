
#!/usr/bin/env bash

# ==========================================================
# IAC Converter - Linux Installation Script
# Requires Python 3.11+
# ==========================================================

set -Eeuo pipefail

APP_NAME="iac-converter"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/$APP_NAME"

echo
echo "=========================================="
echo "       IAC Converter Installation"
echo "=========================================="
echo

# ----------------------------------------------------------
# Error handler
# ----------------------------------------------------------

handle_error() {
    echo
    echo "Installation failed."
    echo "Check the error message above and try again."
    exit 1
}

trap handle_error ERR

# ----------------------------------------------------------
# Check project directory
# ----------------------------------------------------------

if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    echo "ERROR: pyproject.toml not found."
    echo "Run this script from the IAC Converter repository."
    exit 1
fi

echo "[1/7] Checking project directory..."
echo "$PROJECT_ROOT"

# ----------------------------------------------------------
# Check Python
# ----------------------------------------------------------

echo
echo "[2/7] Checking Python installation..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    echo "Install Python 3.11 or newer."
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "ERROR: Python 3.11 or newer is required."
    python3 --version
    exit 1
fi

python3 --version

# ----------------------------------------------------------
# Create virtual environment
# ----------------------------------------------------------

echo
echo "[3/7] Preparing virtual environment..."

if [[ ! -x "$VENV_PYTHON" ]]; then
    python3 -m venv "$VENV_DIR"
else
    echo "Existing virtual environment found. Reusing it."
fi

# ----------------------------------------------------------
# Install application
# ----------------------------------------------------------

echo
echo "[4/7] Installing IAC Converter..."

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install "$PROJECT_ROOT"

# ----------------------------------------------------------
# Create command launcher
# ----------------------------------------------------------

echo
echo "[5/7] Creating command launcher..."

mkdir -p "$BIN_DIR"

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
exec "$VENV_PYTHON" -m iac_converter.cli "\$@"
EOF

chmod +x "$LAUNCHER"

# ----------------------------------------------------------
# Configure PATH
# ----------------------------------------------------------

echo
echo "[6/7] Configuring PATH..."

PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

SHELL_NAME="$(basename "${SHELL:-bash}")"

case "$SHELL_NAME" in
    zsh)
        SHELL_CONFIG="$HOME/.zshrc"
        ;;
    bash)
        if [[ -f "$HOME/.bashrc" ]]; then
            SHELL_CONFIG="$HOME/.bashrc"
        else
            SHELL_CONFIG="$HOME/.profile"
        fi
        ;;
    *)
        SHELL_CONFIG="$HOME/.profile"
        ;;
esac

touch "$SHELL_CONFIG"

if ! grep -Fqx "$PATH_LINE" "$SHELL_CONFIG"; then
    {
        echo
        echo "# IAC Converter"
        echo "$PATH_LINE"
    } >> "$SHELL_CONFIG"
fi

# Make command available in current shell.
export PATH="$BIN_DIR:$PATH"

# ----------------------------------------------------------
# Verify installation
# ----------------------------------------------------------

echo
echo "[7/7] Verifying installation..."

"$LAUNCHER" --version

echo
"$LAUNCHER" --help >/dev/null

echo "CLI verification successful."

# ----------------------------------------------------------
# Installation summary
# ----------------------------------------------------------

echo
echo "=========================================="
echo " INSTALLATION COMPLETED SUCCESSFULLY"
echo "=========================================="
echo
echo "Application : IAC Converter"
echo "Version     : $("$LAUNCHER" --version)"
echo "Python      : $VENV_PYTHON"
echo "Launcher    : $LAUNCHER"
echo "PATH config : $SHELL_CONFIG"
echo
echo "Restart your terminal or run:"
echo "source \"$SHELL_CONFIG\""
echo
echo "Test the application:"
echo "$APP_NAME --version"
echo "$APP_NAME --help"
echo
echo "=========================================="
