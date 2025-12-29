"""File iteration utilities"""

from pathlib import Path
from typing import Iterator, List
import fnmatch
import logging

from ..models.config import ScanConfig

logger = logging.getLogger(__name__)


class FileIterator:
    """Iterates over files in a directory tree with filtering"""
    
    # Common directories to ignore during traversal
    IGNORED_DIRS = {
        'node_modules', 'venv', 'env', '.venv', '.git', 
        '__pycache__', 'dist', 'build', 'site-packages',
        'eggs', '.eggs', '.tox', '.mypy_cache', '.pytest_cache'
    }
    
    def __init__(self, config: ScanConfig):
        self.config = config
    
    def iter_files(self) -> Iterator[Path]:
        """
        Iterate over files matching scan criteria
        
        Yields:
            Path objects for files to scan
        """
        count = 0
        max_files = self.config.max_files
        
        for file_path in self._walk_directory(self.config.root_path):
            # Check if should be excluded
            if self._should_exclude(file_path):
                continue
            
            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size > self.config.max_file_size:
                    if self.config.verbose:
                        logger.info(f"⏭️  Skipping {file_path.name} (too large: {file_size / 1_000_000:.1f}MB)")
                    continue
            except OSError:
                continue
            
            if self.config.verbose:
                logger.info(f"✓ Found: {file_path.relative_to(self.config.root_path)}")
            
            yield file_path
            
            count += 1
            if max_files and count >= max_files:
                break
    
    def _walk_directory(self, path: Path) -> Iterator[Path]:
        """Recursively walk directory tree"""
        try:
            for item in path.iterdir():
                if item.is_file():
                    yield item
                elif item.is_dir():
                    # Skip hidden dirs and common ignored dirs
                    if item.name.startswith('.') or item.name in self.IGNORED_DIRS:
                        continue
                    yield from self._walk_directory(item)
        except PermissionError:
            pass
    
    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns"""
        path_str = str(file_path)
        
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                if self.config.verbose:
                    logger.info(f"Skipping {path_str} (matches {pattern})")
                return True
        
        # Check if file extension is supported
        suffix = file_path.suffix
        name = file_path.name
        
        if name in self.config.docker_files:
            return False
            
        supported = (
            self.config.python_extensions |
            self.config.js_extensions |
            self.config.config_extensions
        )
        
        return suffix not in supported
