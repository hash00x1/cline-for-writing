#!/bin/bash
# Setup script for paragraph embeddings MCP service
# Optimized for Apple M2 with 8GB RAM

set -e

echo "Setting up Paragraph Embeddings MCP Service..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3.9+ is available
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
    echo "Error: Python 3.9+ is required. Found: $python_version"
    echo "Please install Python 3.9 or later."
    exit 1
fi

echo "✓ Python version check passed: $python_version"

# Check if we're on Apple Silicon
if [[ $(uname -m) == "arm64" ]]; then
    echo "✓ Detected Apple Silicon (ARM64)"
    export PYTORCH_ENABLE_MPS_FALLBACK=1
else
    echo "⚠ Not on Apple Silicon, will use CPU"
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install PyTorch with MPS support for Apple Silicon
echo "Installing PyTorch..."
if [[ $(uname -m) == "arm64" ]]; then
    pip install torch torchvision torchaudio
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install sentence-transformers
echo "Installing sentence-transformers..."
pip install sentence-transformers

# Install other requirements
echo "Installing other dependencies..."
pip install -r requirements.txt

# Download and setup NLTK data
echo "Setting up NLTK data..."
python3 -c "
import nltk
try:
    nltk.download('punkt', quiet=True)
    print('✓ NLTK punkt data downloaded')
except Exception as e:
    print(f'⚠ NLTK download failed: {e}')
"

# Try to download the embedding model
echo "Pre-downloading embedding model..."
python3 -c "
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print('✓ Embedding model downloaded successfully')
except Exception as e:
    print(f'⚠ Model download failed: {e}')
    print('Model will be downloaded on first use')
"

# Create cache directory
echo "Creating cache directory..."
python3 -c "
from config import Config
Config.ensure_cache_dir()
print(f'✓ Cache directory created at: {Config.CACHE_DIR}')
"

# Make the server script executable
chmod +x paragraph_embeddings_server.py

# Test the installation
echo "Testing installation..."
python3 -c "
import sys
try:
    import torch
    print(f'✓ PyTorch {torch.__version__}')
    
    import sentence_transformers
    print(f'✓ sentence-transformers {sentence_transformers.__version__}')
    
    # Test MPS availability
    if torch.backends.mps.is_available():
        print('✓ MPS (Apple Silicon GPU) available')
    else:
        print('⚠ MPS not available, will use CPU')
    
    from embedding_manager import EmbeddingManager
    print('✓ Custom modules import successfully')
    
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Add the MCP server to your cline_mcp_settings.json:"
echo ""
echo "{"
echo "  \"mcpServers\": {"
echo "    \"paragraph-embeddings\": {"
echo "      \"command\": \"python\","
echo "      \"args\": [\"$(pwd)/paragraph_embeddings_server.py\"],"
echo "      \"cwd\": \"$(pwd)\","
echo "      \"env\": {"
echo "        \"PYTHONPATH\": \"$(pwd)\""
echo "      },"
echo "      \"disabled\": false,"
echo "      \"autoApprove\": ["
echo "        \"embed_paragraphs\","
echo "        \"search_paragraphs\","
echo "        \"update_embeddings\","
echo "        \"delete_embeddings\","
echo "        \"get_embedding_stats\""
echo "      ]"
echo "    }"
echo "  }"
echo "}"
echo ""
echo "2. Restart Cline for Writers to load the new MCP server"
echo "3. Use the tools in your writing workflow!"
echo ""
echo "Cache directory: $(python3 -c 'from config import Config; print(Config.CACHE_DIR)')"
echo "Log file: $(pwd)/paragraph_embeddings.log"
