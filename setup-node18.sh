#!/bin/bash

# Setup Node.js 18 environment for Cline development
echo "🔧 Setting up Node.js 18 environment for Cline..."

# Check if Node.js 18 is installed
if ! command -v /usr/local/opt/node@18/bin/node &> /dev/null; then
    echo "❌ Node.js 18 not found. Installing with Homebrew..."
    brew install node@18
fi

# Export Node.js 18 to PATH
export PATH="/usr/local/opt/node@18/bin:$PATH"

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Add to shell profile if not already added
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [[ -n "$SHELL_RC" ]]; then
    if ! grep -q "node@18/bin" "$SHELL_RC"; then
        echo 'export PATH="/usr/local/opt/node@18/bin:$PATH"' >> "$SHELL_RC"
        echo "✅ Added Node.js 18 to $SHELL_RC"
    else
        echo "✅ Node.js 18 already in $SHELL_RC"
    fi
fi

echo "🚀 Node.js 18 environment is ready!"
echo ""
echo "To use Node.js 18 in new terminals, run:"
echo "  source $SHELL_RC"
echo ""
echo "Or restart your terminal."
