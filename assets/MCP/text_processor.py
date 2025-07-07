"""
Text processing utilities for paragraph extraction and preprocessing.
Optimized for writing-focused content.
"""

import re
import hashlib
from typing import List, Dict, Any
from pathlib import Path
try:
    import frontmatter
except ImportError:
    frontmatter = None
try:
    import nltk
    from nltk.tokenize import sent_tokenize
except ImportError:
    nltk = None
    sent_tokenize = None
from config import Config

try:
    from latex_parser import LaTeXParser
except ImportError:
    LaTeXParser = None

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class TextProcessor:
    """Handles text extraction and paragraph-level chunking."""
    
    def __init__(self):
        self.config = Config()
        
        # Initialize LaTeX parser if available
        if LaTeXParser:
            self.latex_parser = LaTeXParser()
        else:
            self.latex_parser = None
    
    def extract_paragraphs_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract paragraphs from a file with metadata.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of paragraph dictionaries with metadata
        """
        try:
            file_path = Path(file_path)
            
            # Check if file exists and is supported
            if not file_path.exists() or file_path.suffix.lower() not in self.config.SUPPORTED_EXTENSIONS:
                return []
            
            # Check if it's a LaTeX file
            if self.latex_parser and file_path.suffix.lower() in {'.tex', '.latex'}:
                return self._extract_paragraphs_from_latex(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter if present
            try:
                if frontmatter:
                    post = frontmatter.loads(content)
                    text_content = post.content
                    metadata = post.metadata
                else:
                    text_content = content
                    metadata = {}
            except (UnicodeDecodeError, FileNotFoundError, IOError):
                text_content = content
                metadata = {}
            
            # Extract paragraphs
            paragraphs = self._extract_paragraphs(text_content)
            
            # Create paragraph objects with metadata
            result = []
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) >= self.config.MIN_PARAGRAPH_LENGTH:
                    paragraph_hash = hashlib.md5(paragraph.encode()).hexdigest()
                    
                    result.append({
                        'content': paragraph.strip(),
                        'file_path': str(file_path),
                        'paragraph_index': i,
                        'paragraph_hash': paragraph_hash,
                        'word_count': len(paragraph.split()),
                        'char_count': len(paragraph),
                        'file_metadata': metadata
                    })
            
            return result
            
        except (FileNotFoundError, IOError, OSError) as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return []
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """
        Extract paragraphs from text content.
        
        Args:
            text: Raw text content
            
        Returns:
            List of paragraph strings
        """
        # Remove common markdown elements that aren't content
        text = self._clean_markdown(text)
        
        # Split by double newlines (paragraph boundaries)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Process each paragraph
        processed_paragraphs = []
        for paragraph in paragraphs:
            # Clean and normalize whitespace
            paragraph = re.sub(r'\s+', ' ', paragraph.strip())
            
            # Skip empty paragraphs or those that are too short
            if len(paragraph) < self.config.MIN_PARAGRAPH_LENGTH:
                continue
            
            # Split long paragraphs
            if len(paragraph) > self.config.MAX_PARAGRAPH_LENGTH:
                sub_paragraphs = self._split_long_paragraph(paragraph)
                processed_paragraphs.extend(sub_paragraphs)
            else:
                processed_paragraphs.append(paragraph)
        
        return processed_paragraphs
    
    def _clean_markdown(self, text: str) -> str:
        """
        Clean markdown syntax while preserving content structure.
        
        Args:
            text: Raw markdown text
            
        Returns:
            Cleaned text
        """
        # Remove YAML frontmatter (already extracted)
        text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
        
        # Convert headers to regular text (preserve the text, remove the #)
        text = re.sub(r'^#+\s*(.+)$', r'\1', text, flags=re.MULTILINE)
        
        # Remove code blocks but keep inline code
        text = re.sub(r'```[\s\S]*?```', '', text)
        
        # Remove horizontal rules
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
        
        # Convert lists to readable text
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove link syntax but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove image syntax
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        
        # Remove emphasis markers but keep text
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove inline code markers
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Clean up blockquotes
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        return text
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        Split a long paragraph into smaller chunks with overlap.
        
        Args:
            paragraph: Long paragraph to split
            
        Returns:
            List of paragraph chunks
        """
        # Try to split by sentences first
        if sent_tokenize:
            sentences = sent_tokenize(paragraph)
        else:
            # Fallback to simple sentence splitting
            sentences = re.split(r'[.!?]+\s+', paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed max length, start a new chunk
            if len(current_chunk) + len(sentence) > self.config.MAX_PARAGRAPH_LENGTH:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    current_chunk = self._get_overlap_text(current_chunk) + " " + sentence
                else:
                    # Single sentence is too long, just add it
                    chunks.append(sentence)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Get the last part of text for overlap with next chunk.
        
        Args:
            text: Text to get overlap from
            
        Returns:
            Overlap text
        """
        if len(text) <= self.config.OVERLAP_SIZE:
            return text
        
        # Try to find a good breaking point (end of sentence)
        overlap_start = len(text) - self.config.OVERLAP_SIZE
        
        # Look for sentence end within overlap region
        sentence_end = text.rfind('.', overlap_start)
        if sentence_end != -1 and sentence_end > overlap_start:
            return text[sentence_end + 1:].strip()
        
        return text[-self.config.OVERLAP_SIZE:].strip()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate hash of file content for change detection.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash of file content
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except (FileNotFoundError, IOError, OSError):
            return ""
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic statistics about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file statistics
        """
        try:
            file_path = Path(file_path)
            stat = file_path.stat()
            
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'extension': file_path.suffix.lower()
            }
        except (FileNotFoundError, IOError, OSError):
            return {}
    
    def _extract_paragraphs_from_latex(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract paragraphs from LaTeX files.
        
        Args:
            file_path: Path to the LaTeX file
            
        Returns:
            List of paragraph dictionaries
        """
        if not self.latex_parser:
            return []
        
        try:
            # Parse LaTeX file
            latex_result = self.latex_parser.parse_latex_file(str(file_path))
            
            if 'error' in latex_result:
                return []
            
            # Convert to paragraph format
            result = []
            paragraphs = latex_result.get('paragraphs', [])
            
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) >= self.config.MIN_PARAGRAPH_LENGTH:
                    paragraph_hash = hashlib.md5(paragraph.encode()).hexdigest()
                    
                    result.append({
                        'content': paragraph.strip(),
                        'file_path': str(file_path),
                        'paragraph_index': i,
                        'paragraph_hash': paragraph_hash,
                        'word_count': len(paragraph.split()),
                        'char_count': len(paragraph),
                        'file_metadata': {
                            **latex_result.get('metadata', {}),
                            'file_type': 'latex'
                        }
                    })
            
            return result
            
        except (FileNotFoundError, IOError, OSError) as e:
            print(f"Error processing LaTeX file {file_path}: {str(e)}")
            return []
