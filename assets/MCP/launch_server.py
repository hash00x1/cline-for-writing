#!/usr/bin/env python3
"""
Simple launcher for the paragraph embeddings MCP server.
Use this to test the server before integrating with Cline.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set environment variables
os.environ['PYTHONPATH'] = str(current_dir)

if __name__ == "__main__":
    # Import and run the server
    try:
        from paragraph_embeddings_server import main
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
