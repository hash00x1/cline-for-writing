# Dynamic Paragraph Embeddings MCP Service

This directory contains a dynamic paragraph-level embeddings system that automatically monitors `.tex` and `.md` files for changes and updates embeddings in real-time. Optimized for Apple M2 with 8GB RAM.

## Architecture

```
┌─────────────────┐    MCP Protocol    ┌──────────────────────┐
│ Cline for       │◄──────────────────►│ paragraph-embeddings │
│ Writers         │                    │ MCP Server           │
└─────────────────┘                    └──────────────────────┘
                                                │
                                                ▼
                                       ┌──────────────────────┐
                                       │ File Watcher         │
                                       │ (.md, .tex files)    │
                                       └──────────────────────┘
                                                │
                                                ▼
                                       ┌──────────────────────┐
                                       │ Local Vector Store   │
                                       │ (SQLite + VSS)       │
                                       └──────────────────────┘
                                                │
                                                ▼
                                       ┌──────────────────────┐
                                       │ Embedding Model      │
                                       │ (sentence-transformers│
                                       │ all-MiniLM-L6-v2)    │
                                       └──────────────────────┘
```

## Key Features

- **Dynamic File Watching**: Automatically detects changes to `.tex` and `.md` files
- **Real-time Updates**: Embeddings update when files are modified
- **Apple M2 Optimized**: Uses MPS (Metal Performance Shaders) acceleration
- **Memory Efficient**: Batched processing with configurable batch sizes
- **LaTeX Support**: Parses LaTeX files and extracts meaningful text content
- **Paragraph-Level**: Intelligent text chunking at paragraph boundaries
- **Fast Vector Search**: SQLite with vector similarity search extension

## Components

1. **`paragraph_embeddings_server.py`** - Main MCP server implementation
2. **`embedding_manager.py`** - Core embedding and indexing logic
3. **`text_processor.py`** - Paragraph extraction and preprocessing for .md and .tex files
4. **`vector_store.py`** - SQLite vector storage and search
5. **`file_watcher.py`** - Dynamic file monitoring system
6. **`latex_parser.py`** - LaTeX file parsing and text extraction
7. **`requirements.txt`** - Python dependencies
8. **`config.py`** - Configuration settings

## Installation

```bash
cd assets/MCP
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

## Usage

Add to your `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "paragraph-embeddings": {
      "command": "python",
      "args": ["assets/MCP/paragraph_embeddings_server.py"],
      "cwd": ".",
      "env": {
        "PYTHONPATH": "assets/MCP"
      },
      "disabled": false,
      "autoApprove": [
        "embed_paragraphs",
        "search_paragraphs",
        "update_embeddings",
        "delete_embeddings",
        "get_embedding_stats"
      ]
    }
  }
}
```

## Tools Available

- `start_watching`: Start monitoring a directory for .tex and .md file changes
- `stop_watching`: Stop monitoring file changes
- `search_paragraphs`: Semantic search across all indexed paragraphs
- `get_similar_content`: Find content similar to a specific file or text
- `update_file`: Manually update embeddings for a specific file
- `get_embedding_stats`: Get statistics about the embedding database
- `list_watched_files`: Show currently monitored files
