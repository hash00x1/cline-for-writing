"""
Vector store implementation using SQLite with VSS extension.
Optimized for Apple M2 with 8GB RAM.
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging
from config import Config

class VectorStore:
    """SQLite-based vector store with similarity search capabilities."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the vector store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.config = Config()
        self.config.ensure_cache_dir()
        self.db_path = db_path or str(self.config.DB_FILE)
        self.connection = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with vector search support."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA temp_store=MEMORY")
            self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Try to load VSS extension
            try:
                self.connection.enable_load_extension(True)
                self.connection.load_extension("vss0")
                self.has_vss = True
            except sqlite3.OperationalError:
                logging.warning("VSS extension not available, falling back to cosine similarity")
                self.has_vss = False
                self.connection.enable_load_extension(False)
            
            self._create_tables()
            
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary tables for storing embeddings."""
        # Main paragraphs table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS paragraphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                paragraph_index INTEGER NOT NULL,
                paragraph_hash TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                word_count INTEGER,
                char_count INTEGER,
                file_metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Embeddings table
        if self.has_vss:
            # Use VSS virtual table for vector similarity search
            self.connection.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vss0(
                    paragraph_id INTEGER PRIMARY KEY,
                    embedding({self.config.VECTOR_DIMENSION})
                )
            """)
        else:
            # Fallback table for manual cosine similarity
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    paragraph_id INTEGER PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id)
                )
            """)
        
        # File hashes for change detection
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                hash_value TEXT NOT NULL,
                last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_paragraphs_file_path 
            ON paragraphs(file_path)
        """)
        
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_paragraphs_hash 
            ON paragraphs(paragraph_hash)
        """)
        
        self.connection.commit()
    
    def store_paragraphs(self, paragraphs: List[Dict[str, Any]], embeddings: np.ndarray) -> List[int]:
        """
        Store paragraphs and their embeddings.
        
        Args:
            paragraphs: List of paragraph dictionaries
            embeddings: Numpy array of embeddings
            
        Returns:
            List of paragraph IDs
        """
        if len(paragraphs) != len(embeddings):
            raise ValueError("Number of paragraphs must match number of embeddings")
        
        paragraph_ids = []
        
        try:
            for paragraph, embedding in zip(paragraphs, embeddings):
                # Store paragraph
                cursor = self.connection.execute("""
                    INSERT OR REPLACE INTO paragraphs 
                    (file_path, paragraph_index, paragraph_hash, content, word_count, char_count, file_metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    paragraph['file_path'],
                    paragraph['paragraph_index'],
                    paragraph['paragraph_hash'],
                    paragraph['content'],
                    paragraph['word_count'],
                    paragraph['char_count'],
                    json.dumps(paragraph.get('file_metadata', {}))
                ))
                
                paragraph_id = cursor.lastrowid
                paragraph_ids.append(paragraph_id)
                
                # Store embedding
                if self.has_vss:
                    self.connection.execute("""
                        INSERT OR REPLACE INTO embeddings (paragraph_id, embedding)
                        VALUES (?, ?)
                    """, (paragraph_id, embedding.tobytes()))
                else:
                    self.connection.execute("""
                        INSERT OR REPLACE INTO embeddings (paragraph_id, embedding)
                        VALUES (?, ?)
                    """, (paragraph_id, embedding.tobytes()))
            
            self.connection.commit()
            return paragraph_ids
            
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Failed to store paragraphs: {e}")
            raise
    
    def search_similar(self, query_embedding: np.ndarray, limit: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar paragraphs using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of similar paragraphs with scores
        """
        if limit is None:
            limit = self.config.MAX_SEARCH_RESULTS
        
        try:
            if self.has_vss:
                return self._search_with_vss(query_embedding, limit)
            else:
                return self._search_with_cosine(query_embedding, limit)
                
        except Exception as e:
            logging.error(f"Search failed: {e}")
            return []
    
    def _search_with_vss(self, query_embedding: np.ndarray, limit: int) -> List[Dict[str, Any]]:
        """Search using VSS extension."""
        cursor = self.connection.execute("""
            SELECT 
                p.id,
                p.file_path,
                p.paragraph_index,
                p.content,
                p.word_count,
                p.char_count,
                p.file_metadata,
                vss_search(e.embedding, ?) as score
            FROM paragraphs p
            JOIN embeddings e ON p.id = e.paragraph_id
            WHERE vss_search(e.embedding, ?) IS NOT NULL
            ORDER BY score DESC
            LIMIT ?
        """, (query_embedding.tobytes(), query_embedding.tobytes(), limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'file_path': row[1],
                'paragraph_index': row[2],
                'content': row[3],
                'word_count': row[4],
                'char_count': row[5],
                'file_metadata': json.loads(row[6]) if row[6] else {},
                'similarity_score': row[7]
            })
        
        return results
    
    def _search_with_cosine(self, query_embedding: np.ndarray, limit: int) -> List[Dict[str, Any]]:
        """Search using manual cosine similarity calculation."""
        cursor = self.connection.execute("""
            SELECT 
                p.id,
                p.file_path,
                p.paragraph_index,
                p.content,
                p.word_count,
                p.char_count,
                p.file_metadata,
                e.embedding
            FROM paragraphs p
            JOIN embeddings e ON p.id = e.paragraph_id
        """)
        
        results_with_scores = []
        query_norm = np.linalg.norm(query_embedding)
        
        for row in cursor.fetchall():
            # Deserialize embedding
            embedding = np.frombuffer(row[7], dtype=np.float32)
            
            # Calculate cosine similarity
            dot_product = np.dot(query_embedding, embedding)
            embedding_norm = np.linalg.norm(embedding)
            
            if embedding_norm == 0:
                similarity = 0
            else:
                similarity = dot_product / (query_norm * embedding_norm)
            
            # Only include results above threshold
            if similarity >= self.config.SIMILARITY_THRESHOLD:
                results_with_scores.append({
                    'id': row[0],
                    'file_path': row[1],
                    'paragraph_index': row[2],
                    'content': row[3],
                    'word_count': row[4],
                    'char_count': row[5],
                    'file_metadata': json.loads(row[6]) if row[6] else {},
                    'similarity_score': float(similarity)
                })
        
        # Sort by similarity score and limit results
        results_with_scores.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results_with_scores[:limit]
    
    def delete_file_embeddings(self, file_path: str) -> int:
        """
        Delete all embeddings for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of deleted paragraphs
        """
        try:
            # Get paragraph IDs for the file
            cursor = self.connection.execute("""
                SELECT id FROM paragraphs WHERE file_path = ?
            """, (file_path,))
            
            paragraph_ids = [row[0] for row in cursor.fetchall()]
            
            if not paragraph_ids:
                return 0
            
            # Delete embeddings
            placeholders = ','.join(['?' for _ in paragraph_ids])
            self.connection.execute(f"""
                DELETE FROM embeddings WHERE paragraph_id IN ({placeholders})
            """, paragraph_ids)
            
            # Delete paragraphs
            self.connection.execute("""
                DELETE FROM paragraphs WHERE file_path = ?
            """, (file_path,))
            
            # Delete file hash
            self.connection.execute("""
                DELETE FROM file_hashes WHERE file_path = ?
            """, (file_path,))
            
            self.connection.commit()
            return len(paragraph_ids)
            
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Failed to delete embeddings for {file_path}: {e}")
            raise
    
    def update_file_hash(self, file_path: str, hash_value: str):
        """Update the hash for a file."""
        self.connection.execute("""
            INSERT OR REPLACE INTO file_hashes (file_path, hash_value)
            VALUES (?, ?)
        """, (file_path, hash_value))
        self.connection.commit()
    
    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Get the stored hash for a file."""
        cursor = self.connection.execute("""
            SELECT hash_value FROM file_hashes WHERE file_path = ?
        """, (file_path,))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            cursor = self.connection.execute("""
                SELECT 
                    COUNT(*) as total_paragraphs,
                    COUNT(DISTINCT file_path) as total_files,
                    AVG(word_count) as avg_word_count,
                    AVG(char_count) as avg_char_count
                FROM paragraphs
            """)
            
            stats = cursor.fetchone()
            
            return {
                'total_paragraphs': stats[0],
                'total_files': stats[1],
                'avg_word_count': round(stats[2], 2) if stats[2] else 0,
                'avg_char_count': round(stats[3], 2) if stats[3] else 0,
                'has_vss_extension': self.has_vss,
                'db_path': self.db_path
            }
            
        except Exception as e:
            logging.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        self.close()
