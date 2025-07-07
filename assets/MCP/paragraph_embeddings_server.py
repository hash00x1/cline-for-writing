#!/usr/bin/env python3
"""
Paragraph-level local embeddings MCP server.
Optimized for Apple M2 with 8GB RAM.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict
from pathlib import Path
import traceback

# Configure logging
# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, 'paragraph_embeddings.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stderr)
    ]
)

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        Tool,
        TextContent,
    )
    # Try to import error classes - they may be named differently
    try:
        from mcp.types import McpError, ErrorCode
    except ImportError:
        # Fallback: create our own error classes
        class McpError(Exception):
            def __init__(self, code, message):
                self.code = code
                self.message = message
                super().__init__(message)
        
        class ErrorCode:
            INVALID_PARAMS = "INVALID_PARAMS"
            METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
            INTERNAL_ERROR = "INTERNAL_ERROR"
            
except ImportError as e:
    logging.error(f"MCP not available: {e}")
    sys.exit(1)

# Import our custom modules
try:
    from config import Config
    from vector_store import VectorStore
    from embedding_manager import EmbeddingManager
    from file_watcher import FileWatcher
except ImportError as e:
    logging.error(f"Local modules not available: {e}")
    sys.exit(1)

class ParagraphEmbeddingsServer:
    """MCP server for paragraph-level embeddings."""
    
    def __init__(self):
        """Initialize the embeddings server."""
        self.config = Config()
        self.vector_store = VectorStore()
        self.embedding_manager = EmbeddingManager(self.vector_store, self.config)
        self.file_watcher = FileWatcher(self.embedding_manager)
        self.server = Server("paragraph-embeddings")
        
        # Register tools
        self._register_tools()
        
        # Register handlers
        self.server.call_tool = self.handle_call_tool
        self.server.list_tools = self.handle_list_tools
    
    def _register_tools(self):
        """Register available tools."""
        self.tools = [
            Tool(
                name="start_watching",
                description="Start monitoring a directory for .tex and .md file changes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to directory to monitor"
                        }
                    },
                    "required": ["directory_path"]
                }
            ),
            Tool(
                name="stop_watching",
                description="Stop monitoring file changes in a directory or all directories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory to stop watching (optional - stops all if not provided)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="search_paragraphs",
                description="Search for paragraphs similar to a query using semantic search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_similar_content",
                description="Find content similar to a specific file or text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file to find similar content for"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text content to find similar content for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="update_file",
                description="Manually update embeddings for a specific file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to update"
                        },
                        "force_update": {
                            "type": "boolean",
                            "description": "Force update even if file hasn't changed",
                            "default": False
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="get_embedding_stats",
                description="Get statistics about the embedding database and file watcher",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="list_watched_files",
                description="Show currently monitored directories and file statistics",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    async def handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list tools request."""
        return ListToolsResult(tools=self.tools)
    
    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call requests."""
        try:
            # Initialize embedding manager if not already done
            if self.embedding_manager is None:
                self.embedding_manager = EmbeddingManager()
            
            # Route to appropriate handler
            if request.params.name == "start_watching":
                return await self._handle_start_watching(request.params.arguments)
            elif request.params.name == "stop_watching":
                return await self._handle_stop_watching(request.params.arguments)
            elif request.params.name == "search_paragraphs":
                return await self._handle_search_paragraphs(request.params.arguments)
            elif request.params.name == "get_similar_content":
                return await self._handle_get_similar_content(request.params.arguments)
            elif request.params.name == "update_file":
                return await self._handle_update_file(request.params.arguments)
            elif request.params.name == "get_embedding_stats":
                return await self._handle_get_stats(request.params.arguments)
            elif request.params.name == "list_watched_files":
                return await self._handle_list_watched_files(request.params.arguments)
            else:
                raise McpError(
                    ErrorCode.METHOD_NOT_FOUND,
                    f"Unknown tool: {request.params.name}"
                )
                
        except Exception as e:
            logging.error(f"Tool call failed: {e}")
            logging.error(traceback.format_exc())
            raise McpError(
                ErrorCode.INTERNAL_ERROR,
                f"Tool execution failed: {str(e)}"
            )
    
    async def _handle_start_watching(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle start_watching tool call."""
        directory_path = arguments.get("directory_path")
        
        if not directory_path:
            raise McpError(ErrorCode.INVALID_PARAMS, "directory_path is required")
        
        # Resolve path
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            raise McpError(ErrorCode.INVALID_PARAMS, f"Directory not found: {directory_path}")
        
        # Start watching
        result = self.embedding_manager.start_watching_directory(str(path))
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        )
    
    async def _handle_stop_watching(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle stop_watching tool call."""
        directory_path = arguments.get("directory_path")
        
        # Stop watching (directory_path is optional)
        result = self.embedding_manager.stop_watching_directory(directory_path)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        )
    
    async def _handle_get_similar_content(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_similar_content tool call."""
        file_path = arguments.get("file_path")
        text = arguments.get("text")
        limit = arguments.get("limit", 5)
        
        if not file_path and not text:
            raise McpError(ErrorCode.INVALID_PARAMS, "Either file_path or text is required")
        
        if file_path:
            # Get content from file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract first paragraph or use first 500 chars
                paragraphs = content.split('\n\n')
                if paragraphs:
                    query_text = paragraphs[0][:500]
                else:
                    query_text = content[:500]
            except Exception as e:
                raise McpError(ErrorCode.INVALID_PARAMS, f"Failed to read file: {e}")
        else:
            query_text = text
        
        # Search for similar content
        results = self.embedding_manager.search_paragraphs(query_text, limit)
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_result = {
                "rank": i,
                "similarity_score": round(result.get("similarity_score", 0), 4),
                "file_path": result.get("file_path", ""),
                "paragraph_index": result.get("paragraph_index", 0),
                "content_preview": result.get("content", "")[:150] + "..." if len(result.get("content", "")) > 150 else result.get("content", ""),
                "word_count": result.get("word_count", 0)
            }
            formatted_results.append(formatted_result)
        
        response = {
            "query_source": "file" if file_path else "text",
            "query_path": file_path if file_path else None,
            "total_results": len(results),
            "results": formatted_results
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(response, indent=2)
                )
            ]
        )
    
    async def _handle_update_file(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle update_file tool call."""
        file_path = arguments.get("file_path")
        force_update = arguments.get("force_update", False)
        
        if not file_path:
            raise McpError(ErrorCode.INVALID_PARAMS, "file_path is required")
        
        # Resolve path
        path = Path(file_path)
        if not path.exists():
            raise McpError(ErrorCode.INVALID_PARAMS, f"File not found: {file_path}")
        
        # Process file
        result = self.embedding_manager.process_file(str(path), force_update)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        )
    
    async def _handle_list_watched_files(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle list_watched_files tool call."""
        watched_dirs = self.embedding_manager.get_watched_directories()
        watcher_stats = self.embedding_manager.get_watcher_stats()
        
        response = {
            "watched_directories": watched_dirs,
            "watcher_statistics": watcher_stats
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(response, indent=2)
                )
            ]
        )
    async def _handle_get_stats(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_embedding_stats tool call."""
        embedding_stats = self.embedding_manager.get_stats()
        watcher_stats = self.embedding_manager.get_watcher_stats()
        
        combined_stats = {
            "embedding_system": embedding_stats,
            "file_watcher": watcher_stats
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(combined_stats, indent=2)
                )
            ]
        )
    
    async def _handle_search_paragraphs(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle search_paragraphs tool call."""
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        
        if not query:
            raise McpError(ErrorCode.INVALID_PARAMS, "query is required")
        
        # Perform search
        results = self.embedding_manager.search_paragraphs(query, limit)
        
        # Format results for display
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_result = {
                    "rank": i,
                    "similarity_score": round(result.get("similarity_score", 0), 4),
                    "file_path": result.get("file_path", ""),
                    "paragraph_index": result.get("paragraph_index", 0),
                    "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                    "word_count": result.get("word_count", 0)
                }
                formatted_results.append(formatted_result)
            
            response = {
                "query": query,
                "total_results": len(results),
                "results": formatted_results
            }
        else:
            response = {
                "query": query,
                "total_results": 0,
                "results": [],
                "message": "No similar paragraphs found"
            }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(response, indent=2)
                )
            ]
        )
    
    async def _handle_update_embeddings(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle update_embeddings tool call."""
        directory_path = arguments.get("directory_path")
        force_update = arguments.get("force_update", False)
        
        if not directory_path:
            raise McpError(ErrorCode.INVALID_PARAMS, "directory_path is required")
        
        # Resolve directory path
        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            raise McpError(ErrorCode.INVALID_PARAMS, f"Directory not found: {directory_path}")
        
        # Find supported files
        supported_files = []
        for ext in self.config.SUPPORTED_EXTENSIONS:
            supported_files.extend(dir_path.rglob(f"*{ext}"))
        
        # Filter out excluded patterns
        filtered_files = []
        for file_path in supported_files:
            exclude = False
            for pattern in self.config.EXCLUDE_PATTERNS:
                if file_path.match(pattern):
                    exclude = True
                    break
            if not exclude:
                filtered_files.append(file_path)
        
        # Process files
        results = {
            "directory": str(dir_path),
            "total_files_found": len(filtered_files),
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "files": []
        }
        
        for file_path in filtered_files:
            file_result = self.embedding_manager.process_file(str(file_path), force_update)
            results["files"].append(file_result)
            
            if file_result["status"] == "success":
                results["processed"] += 1
            elif file_result["status"] == "skipped":
                results["skipped"] += 1
            else:
                results["errors"] += 1
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )
            ]
        )
    
    async def _handle_delete_embeddings(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle delete_embeddings tool call."""
        file_path = arguments.get("file_path")
        
        if not file_path:
            raise McpError(ErrorCode.INVALID_PARAMS, "file_path is required")
        
        # Delete embeddings
        result = self.embedding_manager.delete_file_embeddings(file_path)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        )
    
    async def _handle_get_stats(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_embedding_stats tool call."""
        stats = self.embedding_manager.get_stats()
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(stats, indent=2)
                )
            ]
        )
    
    async def run(self):
        """Run the MCP server."""
        try:
            async with self.server.stdio() as streams:
                await self.server.run(
                    streams[0], 
                    streams[1], 
                    InitializationOptions(
                        server_name="paragraph-embeddings",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logging.error(f"Server error: {e}")
            logging.error(traceback.format_exc())
        finally:
            # Cleanup
            if self.embedding_manager:
                self.embedding_manager.close()

async def main():
    """Main entry point."""
    server = ParagraphEmbeddingsServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
