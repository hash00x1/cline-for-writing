#!/bin/bash
# Script to use Node.js 20 for the current session on M2 Mac

# Set Node.js 20 in PATH
export PATH="/usr/local/Cellar/node@20/20.19.3/bin:$PATH"
export NODE_PATH="/usr/local/Cellar/node@20/20.19.3/lib/node_modules"

# Verify the versions
echo "✅ Switched to Node.js $(node --version)"
echo "✅ npm version: $(npm --version)"
echo "✅ Platform: $(uname -m)"

# If arguments are provided, execute them with Node.js 20
if [ $# -gt 0 ]; then
    echo "🚀 Executing: $@"
    exec "$@"
else
    echo "💡 Usage: ./use-node20.sh [command]"
    echo "💡 Or source this script to set Node.js 20 in current shell: source ./use-node20.sh"
fi
