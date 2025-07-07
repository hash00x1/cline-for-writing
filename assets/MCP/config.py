"""
Configuration settings for the paragraph embeddings MCP service.
Optimized for Apple M2 with 8GB RAM.
"""

import os
import torch
from pathlib import Path

class Config:
    # Model settings - optimized for Apple M2
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Lightweight, fast model
    DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"  # Use Apple Silicon GPU
    
    # Memory management for 8GB RAM
    BATCH_SIZE = 16  # Process 16 paragraphs at a time
    MAX_BATCH_SIZE = 32  # Maximum batch size under memory pressure
    MIN_BATCH_SIZE = 4   # Minimum batch size for efficiency
    
    # Text processing
    MIN_PARAGRAPH_LENGTH = 50  # Minimum characters for a paragraph
    MAX_PARAGRAPH_LENGTH = 2000  # Maximum characters to prevent memory issues
    OVERLAP_SIZE = 100  # Character overlap for long paragraph splits
    
    # Vector store settings
    VECTOR_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2 embeddings
    SIMILARITY_THRESHOLD = 0.7  # Minimum similarity for search results
    MAX_SEARCH_RESULTS = 10  # Maximum results to return
    
    # File watching and caching
    CACHE_DIR = Path.home() / ".cline_embeddings_cache"
    DB_FILE = CACHE_DIR / "embeddings.db"
    HASH_CACHE_FILE = CACHE_DIR / "file_hashes.json"
    
    # Performance settings
    NUM_WORKERS = 2  # Parallel workers for file processing (conservative for 8GB RAM)
    EMBEDDING_CACHE_SIZE = 1000  # Number of embeddings to keep in memory
    
    # File types to process
    SUPPORTED_EXTENSIONS = {'.md', '.tex', '.markdown', '.latex'}
    
    # File watching settings
    WATCH_DEBOUNCE_SECONDS = 2  # Wait 2 seconds after file change before processing
    WATCH_RECURSIVE = True  # Watch subdirectories
    MAX_WATCHED_DIRECTORIES = 10  # Maximum number of directories to watch
    
    # LaTeX-specific settings
    LATEX_COMMANDS_TO_EXTRACT = {
        'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph',
        'chapter', 'part', 'title', 'author', 'abstract', 'textbf', 'textit',
        'emph', 'text', 'caption'
    }
    LATEX_ENVIRONMENTS_TO_EXTRACT = {
        'document', 'abstract', 'figure', 'table', 'equation', 'align',
        'itemize', 'enumerate', 'description', 'quote', 'quotation'
    }
    
    # Exclusion patterns
    EXCLUDE_PATTERNS = {
        '**/.git/**',
        '**/node_modules/**',
        '**/.vscode/**',
        '**/dist/**',
        '**/build/**'
    }
    
    @classmethod
    def adjust_for_memory_pressure(cls):
        """Adjust settings if memory pressure is detected."""
        # Check available memory and adjust batch size
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        
        if available_memory_gb < 2:  # Less than 2GB available
            cls.BATCH_SIZE = cls.MIN_BATCH_SIZE
            cls.NUM_WORKERS = 1
            cls.EMBEDDING_CACHE_SIZE = 500
        elif available_memory_gb < 4:  # Less than 4GB available
            cls.BATCH_SIZE = 8
            cls.NUM_WORKERS = 1
            cls.EMBEDDING_CACHE_SIZE = 750
    
    @classmethod
    def ensure_cache_dir(cls):
        """Ensure cache directory exists."""
        cls.CACHE_DIR.mkdir(exist_ok=True)
        return cls.CACHE_DIR
