#!/bin/bash
# This script ensures that the MCP server is launched with the correct python environment.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
if [ -d "$SCRIPT_DIR/../venv" ]; then
  echo "Activating virtual environment..."
  source "$SCRIPT_DIR/../venv/bin/activate"
else
  echo "Error: Virtual environment not found in $SCRIPT_DIR/../"
  exit 1
fi

# Run the server
python "$SCRIPT_DIR/paragraph_embeddings_server.py"
