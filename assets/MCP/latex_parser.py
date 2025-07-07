"""
LaTeX file parser for extracting meaningful text content.
Optimized for academic and technical writing.
"""

import re
from typing import List, Dict, Any
from pathlib import Path
from config import Config

class LaTeXParser:
    """Parser for LaTeX files to extract meaningful text content."""
    
    def __init__(self):
        self.config = Config()
        
        # Define patterns for LaTeX elements
        self.command_pattern = re.compile(r'\\([a-zA-Z]+)(?:\[[^\]]*\])?\{([^}]*)\}')
        self.environment_pattern = re.compile(r'\\begin\{([^}]+)\}(.*?)\\end\{\1\}', re.DOTALL)
        self.comment_pattern = re.compile(r'(?<!\\)%.*$', re.MULTILINE)
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Commands that should be completely removed
        self.ignore_commands = {
            'usepackage', 'documentclass', 'newcommand', 'renewcommand',
            'def', 'let', 'input', 'include', 'includegraphics', 'cite',
            'ref', 'label', 'index', 'footnote', 'marginpar', 'verb',
            'url', 'href', 'pageref', 'nameref'
        }
        
        # Commands that should have their content extracted
        self.text_commands = self.config.LATEX_COMMANDS_TO_EXTRACT
        
        # Environments to process
        self.text_environments = self.config.LATEX_ENVIRONMENTS_TO_EXTRACT
    
    def parse_latex_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a LaTeX file and extract text content.
        
        Args:
            file_path: Path to the LaTeX file
            
        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from document
            metadata = self._extract_metadata(content)
            
            # Clean and extract text
            text_content = self._extract_text_content(content)
            
            # Split into paragraphs
            paragraphs = self._split_into_paragraphs(text_content)
            
            return {
                'file_path': file_path,
                'file_type': 'latex',
                'metadata': metadata,
                'content': text_content,
                'paragraphs': paragraphs,
                'paragraph_count': len(paragraphs)
            }
            
        except (FileNotFoundError, IOError, OSError, UnicodeDecodeError) as e:
            print(f"Error parsing LaTeX file {file_path}: {str(e)}")
            return {
                'file_path': file_path,
                'file_type': 'latex',
                'metadata': {},
                'content': '',
                'paragraphs': [],
                'paragraph_count': 0,
                'error': str(e)
            }
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from LaTeX document."""
        metadata = {}
        
        # Extract title
        title_match = re.search(r'\\title\{([^}]+)\}', content)
        if title_match:
            metadata['title'] = self._clean_text(title_match.group(1))
        
        # Extract author
        author_match = re.search(r'\\author\{([^}]+)\}', content)
        if author_match:
            metadata['author'] = self._clean_text(author_match.group(1))
        
        # Extract date
        date_match = re.search(r'\\date\{([^}]+)\}', content)
        if date_match:
            metadata['date'] = self._clean_text(date_match.group(1))
        
        # Extract document class
        docclass_match = re.search(r'\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}', content)
        if docclass_match:
            metadata['document_class'] = docclass_match.group(1)
        
        # Count sections
        sections = re.findall(r'\\section\{[^}]+\}', content)
        metadata['section_count'] = len(sections)
        
        # Count subsections
        subsections = re.findall(r'\\subsection\{[^}]+\}', content)
        metadata['subsection_count'] = len(subsections)
        
        return metadata
    
    def _extract_text_content(self, content: str) -> str:
        """Extract readable text content from LaTeX source."""
        # Remove comments
        content = self.comment_pattern.sub('', content)
        
        # Extract text from environments
        content = self._process_environments(content)
        
        # Extract text from commands
        content = self._process_commands(content)
        
        # Remove remaining LaTeX commands
        content = re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})*', '', content)
        
        # Remove math environments
        content = re.sub(r'\$\$.*?\$\$', '[EQUATION]', content, flags=re.DOTALL)
        content = re.sub(r'\$[^$]+\$', '[MATH]', content)
        
        # Remove brackets and braces
        content = re.sub(r'[{}]', '', content)
        content = re.sub(r'\[[^\]]*\]', '', content)
        
        # Clean up whitespace
        content = self.whitespace_pattern.sub(' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def _process_environments(self, content: str) -> str:
        """Process LaTeX environments and extract text."""
        def replace_environment(match):
            env_name = match.group(1)
            env_content = match.group(2)
            
            if env_name in self.text_environments:
                # Recursively process the environment content
                processed_content = self._process_commands(env_content)
                
                # Add context for certain environments
                if env_name == 'abstract':
                    return f"\n\nABSTRACT:\n{processed_content}\n\n"
                elif env_name in ['quote', 'quotation']:
                    return f"\n\nQUOTE:\n{processed_content}\n\n"
                elif env_name == 'figure':
                    # Extract caption if present
                    caption_match = re.search(r'\\caption\{([^}]+)\}', processed_content)
                    if caption_match:
                        return f"\n\nFIGURE: {self._clean_text(caption_match.group(1))}\n\n"
                    return "\n\n[FIGURE]\n\n"
                elif env_name == 'table':
                    # Extract caption if present
                    caption_match = re.search(r'\\caption\{([^}]+)\}', processed_content)
                    if caption_match:
                        return f"\n\nTABLE: {self._clean_text(caption_match.group(1))}\n\n"
                    return "\n\n[TABLE]\n\n"
                else:
                    return processed_content
            else:
                return ''  # Remove unknown environments
        
        return self.environment_pattern.sub(replace_environment, content)
    
    def _process_commands(self, content: str) -> str:
        """Process LaTeX commands and extract text."""
        def replace_command(match):
            command = match.group(1)
            text = match.group(2)
            
            if command in self.ignore_commands:
                return ''
            elif command in self.text_commands:
                cleaned_text = self._clean_text(text)
                
                # Add formatting context for certain commands
                if command in ['section', 'subsection', 'subsubsection']:
                    return f"\n\n{cleaned_text.upper()}\n\n"
                elif command == 'chapter':
                    return f"\n\nCHAPTER: {cleaned_text.upper()}\n\n"
                elif command == 'title':
                    return f"\n\nTITLE: {cleaned_text}\n\n"
                elif command in ['textbf', 'emph']:
                    return f" {cleaned_text} "
                elif command == 'caption':
                    return f"\n\nCAPTION: {cleaned_text}\n\n"
                else:
                    return f" {cleaned_text} "
            else:
                # Unknown command, try to extract text if it looks like text
                if re.match(r'^[a-zA-Z\s]+$', text):
                    return f" {text} "
                return ''
        
        return self.command_pattern.sub(replace_command, content)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove nested commands
        text = re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})*', '', text)
        
        # Remove special characters
        text = re.sub(r'[{}\\]', '', text)
        
        # Normalize whitespace
        text = self.whitespace_pattern.sub(' ', text)
        
        return text.strip()
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs."""
        # Split by double newlines
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Filter and clean paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            
            # Skip empty paragraphs or very short ones
            if len(para) < self.config.MIN_PARAGRAPH_LENGTH:
                continue
            
            # Skip paragraphs that are mostly markup
            if para.count('[') + para.count(']') > len(para) / 4:
                continue
            
            cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def is_latex_file(self, file_path: str) -> bool:
        """Check if a file is a LaTeX file."""
        path = Path(file_path)
        return path.suffix.lower() in {'.tex', '.latex'}
    
    def extract_bibliography_entries(self, content: str) -> List[str]:
        """Extract bibliography entries for reference."""
        # Find bibliography entries
        bib_pattern = re.compile(r'\\bibitem\{[^}]+\}([^\\]+)', re.DOTALL)
        entries = bib_pattern.findall(content)
        
        return [self._clean_text(entry) for entry in entries if entry.strip()]
