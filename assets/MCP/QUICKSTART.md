# Quick Start Guide: Dynamic Paragraph Embeddings MCP Service

## 1. Installation

First, navigate to the MCP directory and run the setup script:

```bash
cd /Users/Lukas_1/cline-for-writing/assets/MCP
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Download the embedding model
- Set up the cache directory

## 2. Configure Cline for Writing

Add the MCP server to your Cline settings. Open your `cline_mcp_settings.json` file (usually in your user settings directory) and add:

```json
{
  "mcpServers": {
    "paragraph-embeddings": {
      "command": "python",
      "args": ["/Users/Lukas_1/cline-for-writing/assets/MCP/paragraph_embeddings_server.py"],
      "cwd": "/Users/Lukas_1/cline-for-writing/assets/MCP",
      "env": {
        "PYTHONPATH": "/Users/Lukas_1/cline-for-writing/assets/MCP"
      },
      "disabled": false,
      "autoApprove": [
        "start_watching",
        "stop_watching", 
        "search_paragraphs",
        "get_similar_content",
        "update_file",
        "get_embedding_stats",
        "list_watched_files"
      ]
    }
  }
}
```

## 3. Test the Server (Optional)

You can test the server directly before connecting to Cline:

```bash
cd /Users/Lukas_1/cline-for-writing/assets/MCP
source venv/bin/activate
python paragraph_embeddings_server.py
```

The server should start and wait for MCP protocol messages on stdin.

## 4. Start Using with Cline

1. **Restart Cline for Writing** to load the new MCP server
2. **Start watching your writing directory**:
   ```
   Use the start_watching tool to monitor your documents directory
   ```
3. **Search your content**:
   ```
   Use search_paragraphs to find similar content across all your documents
   ```

## 5. Available Tools

Once connected, you'll have access to these tools:

- **`start_watching`** - Start monitoring a directory for .tex and .md file changes
- **`stop_watching`** - Stop monitoring file changes  
- **`search_paragraphs`** - Semantic search across all indexed paragraphs
- **`get_similar_content`** - Find content similar to a specific file or text
- **`update_file`** - Manually update embeddings for a specific file
- **`get_embedding_stats`** - Get statistics about the embedding database
- **`list_watched_files`** - Show currently monitored files

## Example Usage in Cline

1. **Start watching your documents**:
   ```
   start_watching("/path/to/your/writing/documents")
   ```

2. **Search for similar content**:
   ```
   search_paragraphs("character development techniques")
   ```

3. **Check system status**:
   ```
   get_embedding_stats()
   ```

## Troubleshooting

- **Memory issues**: The system is optimized for 8GB RAM. If you experience issues, check the logs at `paragraph_embeddings.log`
- **Model loading**: First run may take time to download the embedding model
- **File permissions**: Ensure the server script is executable
- **Python environment**: Make sure you're using the virtual environment

## Performance Notes

- Files are automatically re-indexed when modified
- Embeddings are stored locally in SQLite with vector search
- Batch processing is optimized for Apple M2 performance
- Memory usage is monitored and adjusted automatically
