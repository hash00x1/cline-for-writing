"""
Dynamic file watcher for monitoring .tex and .md file changes.
Automatically updates embeddings when files are modified.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Set, Callable, Optional, Any, List
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
from config import Config

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events for .tex and .md files."""
    
    def __init__(self, callback: Callable[[str, str], None], supported_extensions: Set[str]):
        """
        Initialize the file change handler.
        
        Args:
            callback: Function to call when a file changes (file_path, event_type)
            supported_extensions: Set of file extensions to monitor
        """
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.debounce_map: Dict[str, float] = {}
        self.config = Config()
        
    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in self.supported_extensions:
            return False
        
        # Check exclusion patterns
        for pattern in self.config.EXCLUDE_PATTERNS:
            if path.match(pattern):
                return False
        
        return True
    
    def _debounce_event(self, file_path: str) -> bool:
        """
        Debounce file events to avoid processing rapid successive changes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if event should be processed, False if debounced
        """
        current_time = time.time()
        last_time = self.debounce_map.get(file_path, 0)
        
        if current_time - last_time >= self.config.WATCH_DEBOUNCE_SECONDS:
            self.debounce_map[file_path] = current_time
            return True
        
        return False
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not isinstance(event, FileModifiedEvent) or event.is_directory:
            return
        
        if self._should_process_file(event.src_path) and self._debounce_event(event.src_path):
            logging.info(f"File modified: {event.src_path}")
            self.callback(event.src_path, "modified")
    
    def on_created(self, event):
        """Handle file creation events."""
        if not isinstance(event, FileCreatedEvent) or event.is_directory:
            return
        
        if self._should_process_file(event.src_path):
            logging.info(f"File created: {event.src_path}")
            self.callback(event.src_path, "created")
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not isinstance(event, FileDeletedEvent) or event.is_directory:
            return
        
        if self._should_process_file(event.src_path):
            logging.info(f"File deleted: {event.src_path}")
            self.callback(event.src_path, "deleted")

class DynamicFileWatcher:
    """Manages file watching for multiple directories."""
    
    def __init__(self, embedding_manager=None):
        """
        Initialize the file watcher.
        
        Args:
            embedding_manager: EmbeddingManager instance for processing files
        """
        self.config = Config()
        self.embedding_manager = embedding_manager
        self.observers: Dict[str, Observer] = {}
        self.watched_directories: Set[str] = set()
        self.is_running = False
        
        # Queue for processing file changes
        self.change_queue: asyncio.Queue = asyncio.Queue()
        self.processor_task: Optional[asyncio.Task] = None
    
    def start_watching(self, directory_path: str) -> Dict[str, Any]:
        """
        Start watching a directory for file changes.
        
        Args:
            directory_path: Path to directory to watch
            
        Returns:
            Result dictionary
        """
        try:
            dir_path = Path(directory_path).resolve()
            
            if not dir_path.exists() or not dir_path.is_dir():
                return {
                    'status': 'error',
                    'reason': f'Directory not found: {directory_path}'
                }
            
            dir_str = str(dir_path)
            
            if dir_str in self.watched_directories:
                return {
                    'status': 'info',
                    'reason': f'Directory already being watched: {directory_path}'
                }
            
            if len(self.watched_directories) >= self.config.MAX_WATCHED_DIRECTORIES:
                return {
                    'status': 'error',
                    'reason': f'Maximum number of watched directories ({self.config.MAX_WATCHED_DIRECTORIES}) reached'
                }
            
            # Create file handler
            handler = FileChangeHandler(
                callback=self._queue_file_change,
                supported_extensions=self.config.SUPPORTED_EXTENSIONS
            )
            
            # Create and start observer
            observer = Observer()
            observer.schedule(handler, dir_str, recursive=self.config.WATCH_RECURSIVE)
            observer.start()
            
            # Store observer
            self.observers[dir_str] = observer
            self.watched_directories.add(dir_str)
            
            # Start processor task if not running
            if not self.is_running:
                self.is_running = True
                self.processor_task = asyncio.create_task(self._process_changes())
            
            # Initial scan of existing files
            initial_files = self._scan_directory(dir_path)
            
            logging.info(f"Started watching directory: {dir_str}")
            
            return {
                'status': 'success',
                'directory': dir_str,
                'files_found': len(initial_files),
                'recursive': self.config.WATCH_RECURSIVE
            }
            
        except Exception as e:
            logging.error(f"Failed to start watching {directory_path}: {e}")
            return {
                'status': 'error',
                'reason': str(e)
            }
    
    def stop_watching(self, directory_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop watching a directory or all directories.
        
        Args:
            directory_path: Specific directory to stop watching, or None for all
            
        Returns:
            Result dictionary
        """
        try:
            if directory_path:
                dir_path = str(Path(directory_path).resolve())
                
                if dir_path not in self.watched_directories:
                    return {
                        'status': 'info',
                        'reason': f'Directory not being watched: {directory_path}'
                    }
                
                # Stop observer
                observer = self.observers.pop(dir_path)
                observer.stop()
                observer.join()
                
                self.watched_directories.remove(dir_path)
                
                logging.info(f"Stopped watching directory: {dir_path}")
                
                return {
                    'status': 'success',
                    'directory': dir_path,
                    'action': 'stopped'
                }
            else:
                # Stop all watchers
                stopped_dirs = list(self.watched_directories)
                
                for observer in self.observers.values():
                    observer.stop()
                
                for observer in self.observers.values():
                    observer.join()
                
                self.observers.clear()
                self.watched_directories.clear()
                
                # Stop processor task
                if self.processor_task and not self.processor_task.done():
                    self.processor_task.cancel()
                    self.is_running = False
                
                logging.info("Stopped all file watchers")
                
                return {
                    'status': 'success',
                    'directories_stopped': stopped_dirs,
                    'action': 'stopped_all'
                }
                
        except Exception as e:
            logging.error(f"Failed to stop watching: {e}")
            return {
                'status': 'error',
                'reason': str(e)
            }
    
    def _queue_file_change(self, file_path: str, event_type: str):
        """Queue a file change for processing."""
        try:
            self.change_queue.put_nowait((file_path, event_type, time.time()))
        except asyncio.QueueFull:
            logging.warning(f"Change queue full, dropping event for {file_path}")
    
    async def _process_changes(self):
        """Process queued file changes."""
        while self.is_running:
            try:
                # Wait for a change with timeout
                file_path, event_type, timestamp = await asyncio.wait_for(
                    self.change_queue.get(),
                    timeout=1.0
                )
                
                await self._handle_file_change(file_path, event_type)
                
            except asyncio.TimeoutError:
                # No changes to process, continue
                continue
            except Exception as e:
                logging.error(f"Error processing file change: {e}")
    
    async def _handle_file_change(self, file_path: str, event_type: str):
        """Handle a single file change."""
        if not self.embedding_manager:
            logging.warning("No embedding manager available to process file changes")
            return
        
        try:
            if event_type == "deleted":
                # Remove embeddings for deleted file
                result = self.embedding_manager.delete_file_embeddings(file_path)
                logging.info(f"Deleted embeddings for {file_path}: {result}")
            else:
                # Update embeddings for modified/created file
                result = self.embedding_manager.process_file(file_path, force_update=True)
                logging.info(f"Updated embeddings for {file_path}: {result}")
                
        except Exception as e:
            logging.error(f"Failed to handle file change for {file_path}: {e}")
    
    def _scan_directory(self, directory: Path) -> List[str]:
        """Scan directory for existing supported files."""
        files = []
        
        for ext in self.config.SUPPORTED_EXTENSIONS:
            if self.config.WATCH_RECURSIVE:
                pattern = f"**/*{ext}"
            else:
                pattern = f"*{ext}"
            
            for file_path in directory.glob(pattern):
                # Check exclusion patterns
                exclude = False
                for exclude_pattern in self.config.EXCLUDE_PATTERNS:
                    if file_path.match(exclude_pattern):
                        exclude = True
                        break
                
                if not exclude:
                    files.append(str(file_path))
        
        return files
    
    def get_watched_directories(self) -> List[Dict[str, Any]]:
        """Get list of currently watched directories."""
        return [
            {
                'directory': directory,
                'is_active': directory in self.observers,
                'recursive': self.config.WATCH_RECURSIVE
            }
            for directory in self.watched_directories
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        return {
            'watched_directories_count': len(self.watched_directories),
            'max_watched_directories': self.config.MAX_WATCHED_DIRECTORIES,
            'is_running': self.is_running,
            'queue_size': self.change_queue.qsize(),
            'debounce_seconds': self.config.WATCH_DEBOUNCE_SECONDS,
            'recursive_watching': self.config.WATCH_RECURSIVE,
            'supported_extensions': list(self.config.SUPPORTED_EXTENSIONS)
        }
    
    def close(self):
        """Clean up resources."""
        self.stop_watching()
    
    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        try:
            self.close()
        except Exception:
            pass
