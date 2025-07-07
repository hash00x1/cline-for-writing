"""
Embedding manager for generating and managing embeddings.
Optimized for Apple M2 with 8GB RAM.
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import gc
import psutil
from pathlib import Path
from config import Config
from text_processor import TextProcessor
from vector_store import VectorStore

try:
    from file_watcher import DynamicFileWatcher
except ImportError:
    DynamicFileWatcher = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class EmbeddingManager:
    """Manages embedding generation and storage."""
    
    def __init__(self):
        """Initialize the embedding manager."""
        self.config = Config()
        self.text_processor = TextProcessor()
        self.vector_store = VectorStore()
        self.model = None
        self.file_watcher = None
        
        # Initialize file watcher if available
        if DynamicFileWatcher:
            self.file_watcher = DynamicFileWatcher(embedding_manager=self)
        
        self._load_model()
        
        # Adjust settings based on memory pressure
        self.config.adjust_for_memory_pressure()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        if not SentenceTransformer:
            raise ImportError("sentence-transformers not available. Please install it.")
        
        try:
            logging.info(f"Loading model {self.config.EMBEDDING_MODEL} on device {self.config.DEVICE}")
            
            self.model = SentenceTransformer(
                self.config.EMBEDDING_MODEL,
                device=self.config.DEVICE
            )
            
            # Set model to evaluation mode for inference
            self.model.eval()
            
            # Enable MPS optimization for Apple Silicon
            if self.config.DEVICE == "mps":
                torch.backends.mps.empty_cache()
            
            logging.info("Model loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            # Check memory before processing
            self._check_memory_pressure()
            
            # Adjust batch size based on current memory
            current_batch_size = self._get_optimal_batch_size(len(texts))
            
            all_embeddings = []
            
            # Process in batches to manage memory
            for i in range(0, len(texts), current_batch_size):
                batch = texts[i:i + current_batch_size]
                
                with torch.no_grad():
                    batch_embeddings = self.model.encode(
                        batch,
                        batch_size=current_batch_size,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True  # Normalize for better similarity search
                    )
                
                all_embeddings.append(batch_embeddings)
                
                # Clear cache after each batch
                if self.config.DEVICE == "mps":
                    torch.backends.mps.empty_cache()
                elif self.config.DEVICE == "cuda":
                    torch.cuda.empty_cache()
                
                # Force garbage collection
                gc.collect()
            
            # Concatenate all embeddings
            if all_embeddings:
                result = np.vstack(all_embeddings)
            else:
                result = np.array([])
            
            logging.info(f"Generated {len(result)} embeddings")
            return result
            
        except Exception as e:
            logging.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _check_memory_pressure(self):
        """Check if system is under memory pressure and adjust accordingly."""
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            if available_gb < 1.5:  # Less than 1.5GB available
                logging.warning(f"Low memory detected: {available_gb:.1f}GB available")
                self.config.BATCH_SIZE = self.config.MIN_BATCH_SIZE
                gc.collect()
                if self.config.DEVICE == "mps":
                    torch.backends.mps.empty_cache()
                elif self.config.DEVICE == "cuda":
                    torch.cuda.empty_cache()
        except Exception as e:
            logging.warning(f"Failed to check memory pressure: {e}")

    def _get_optimal_batch_size(self, num_texts: int) -> int:
        """
        Get optimal batch size based on current conditions.
        
        Args:
            num_texts: Number of texts to process
            
        Returns:
            Optimal batch size
        """
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            if available_gb > 4:
                batch_size = min(self.config.MAX_BATCH_SIZE, num_texts)
            elif available_gb > 2:
                batch_size = min(self.config.BATCH_SIZE, num_texts)
            else:
                batch_size = min(self.config.MIN_BATCH_SIZE, num_texts)
            return max(1, batch_size)
        except Exception as e:
            logging.warning(f"Failed to determine optimal batch size: {e}")
            return min(self.config.MIN_BATCH_SIZE, num_texts)

    def process_file(self, file_path: str, force_update: bool = False) -> Dict[str, Any]:
        """
        Process a single file and store its embeddings.
        
        Args:
            file_path: Path to the file to process
            force_update: Force update even if file hasn't changed
            
        Returns:
            Dictionary with processing results
        """
        try:
            file_path = str(Path(file_path).resolve())
            
            # Check if file needs processing
            current_hash = self.text_processor.calculate_file_hash(file_path)
            stored_hash = self.vector_store.get_file_hash(file_path)
            
            if not force_update and current_hash == stored_hash:
                return {
                    'status': 'skipped',
                    'reason': 'file_unchanged',
                    'file_path': file_path
                }
            
            # Extract paragraphs
            paragraphs = self.text_processor.extract_paragraphs_from_file(file_path)
            
            if not paragraphs:
                return {
                    'status': 'skipped',
                    'reason': 'no_paragraphs',
                    'file_path': file_path
                }
            
            # Generate embeddings
            texts = [p['content'] for p in paragraphs]
            embeddings = self.embed_texts(texts)
            
            if len(embeddings) == 0:
                return {
                    'status': 'error',
                    'reason': 'embedding_failed',
                    'file_path': file_path
                }
            
            # Delete existing embeddings for this file
            deleted_count = self.vector_store.delete_file_embeddings(file_path)
            
            # Store new embeddings
            paragraph_ids = self.vector_store.store_paragraphs(paragraphs, embeddings)
            
            # Update file hash
            self.vector_store.update_file_hash(file_path, current_hash)
            
            return {
                'status': 'success',
                'file_path': file_path,
                'paragraphs_processed': len(paragraphs),
                'paragraphs_deleted': deleted_count,
                'paragraph_ids': paragraph_ids
            }
            
        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {e}")
            return {
                'status': 'error',
                'reason': str(e),
                'file_path': file_path
            }
    
    def search_paragraphs(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for paragraphs similar to the query.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of similar paragraphs
        """
        try:
            if not query.strip():
                return []
            
            # Generate query embedding
            query_embedding = self.embed_texts([query])
            
            if len(query_embedding) == 0:
                return []
            
            # Search for similar paragraphs
            results = self.vector_store.search_similar(
                query_embedding[0], 
                limit or self.config.MAX_SEARCH_RESULTS
            )
            
            return results
            
        except Exception as e:
            logging.error(f"Search failed: {e}")
            return []
    
    def delete_file_embeddings(self, file_path: str) -> Dict[str, Any]:
        """
        Delete embeddings for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Deletion results
        """
        try:
            file_path = str(Path(file_path).resolve())
            deleted_count = self.vector_store.delete_file_embeddings(file_path)
            
            return {
                'status': 'success',
                'file_path': file_path,
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            logging.error(f"Failed to delete embeddings for {file_path}: {e}")
            return {
                'status': 'error',
                'reason': str(e),
                'file_path': file_path
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding system."""
        try:
            vector_stats = self.vector_store.get_stats()
            
            # Add system information
            memory = psutil.virtual_memory()
            
            stats = {
                **vector_stats,
                'model_name': self.config.EMBEDDING_MODEL,
                'device': self.config.DEVICE,
                'current_batch_size': self.config.BATCH_SIZE,
                'system_memory_gb': round(memory.total / (1024**3), 2),
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'memory_usage_percent': memory.percent
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Clean up resources."""
        if self.vector_store:
            self.vector_store.close()
        
        # Clear model from memory
        if hasattr(self, 'model') and self.model:
            del self.model
            
        # Clear GPU cache
        if self.config.DEVICE == "mps":
            torch.backends.mps.empty_cache()
        elif self.config.DEVICE == "cuda":
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
    
    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        try:
            self.close()
        except Exception:
            pass
    
    def start_watching_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Start watching a directory for file changes.
        
        Args:
            directory_path: Path to directory to watch
            
        Returns:
            Result dictionary
        """
        if not self.file_watcher:
            return {
                'status': 'error',
                'reason': 'File watcher not available'
            }
        
        return self.file_watcher.start_watching(directory_path)
    
    def stop_watching_directory(self, directory_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop watching a directory or all directories.
        
        Args:
            directory_path: Directory to stop watching, or None for all
            
        Returns:
            Result dictionary
        """
        if not self.file_watcher:
            return {
                'status': 'error',
                'reason': 'File watcher not available'
            }
        
        return self.file_watcher.stop_watching(directory_path)
    
    def get_watched_directories(self) -> List[Dict[str, Any]]:
        """Get list of currently watched directories."""
        if not self.file_watcher:
            return []
        
        return self.file_watcher.get_watched_directories()
    
    def get_watcher_stats(self) -> Dict[str, Any]:
        """Get file watcher statistics."""
        if not self.file_watcher:
            return {'file_watcher': 'not_available'}
        
        return self.file_watcher.get_stats()

    def start_dynamic_watching(self, directory: str):
        """Start dynamic file watching for .md and .tex files in the given directory."""
        if self.file_watcher:
            self.file_watcher.start(directory)
        else:
            logging.warning("DynamicFileWatcher is not available.")

    def stop_dynamic_watching(self):
        """Stop dynamic file watching."""
        if self.file_watcher:
            self.file_watcher.stop()
        else:
            logging.warning("DynamicFileWatcher is not available.")
