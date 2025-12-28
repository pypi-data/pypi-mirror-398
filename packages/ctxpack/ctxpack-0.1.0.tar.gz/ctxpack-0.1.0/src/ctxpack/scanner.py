"""File scanning and discovery for ctxpack."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from ctxpack.config import Config
from ctxpack.ignore import IgnoreMatcher
from ctxpack.utils import is_binary_file, is_test_file


@dataclass
class FileInfo:
    """Information about a discovered file."""
    
    path: Path
    relative_path: str
    size: int
    modified_time: float
    extension: str
    is_test: bool
    
    @property
    def age_hours(self) -> float:
        """Get age in hours since last modification."""
        return (time.time() - self.modified_time) / 3600


def scan_directory(
    root: Path,
    config: Config,
    ignore_matcher: IgnoreMatcher,
    max_scan: int = 10_000,
) -> Generator[FileInfo, None, None]:
    """Scan directory for relevant files.
    
    Args:
        root: Root directory to scan
        config: Configuration with extension filters
        ignore_matcher: Ignore pattern matcher
        max_scan: Maximum files to scan (prevents runaway)
        
    Yields:
        FileInfo for each discovered file
    """
    root = root.resolve()
    extensions = set(config.extensions)
    seen_inodes: set[int] = set()
    file_count = 0
    
    # Use os.walk for iterative traversal (no recursion limit)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        
        # Filter out ignored directories (in-place modification)
        dirnames[:] = [
            d for d in dirnames
            if not ignore_matcher.is_ignored(current / d, root)
        ]
        
        for filename in filenames:
            if file_count >= max_scan:
                return
            
            filepath = current / filename
            
            # Skip if ignored
            if ignore_matcher.is_ignored(filepath, root):
                continue
            
            # Get file extension
            ext = filepath.suffix.lower()
            if not ext or ext not in extensions:
                continue
            
            try:
                stat = filepath.stat()
                
                # Skip symlink loops via inode tracking
                if stat.st_ino in seen_inodes:
                    continue
                seen_inodes.add(stat.st_ino)
                
                # Skip empty files
                if stat.st_size == 0:
                    continue
                
                # Skip binary files
                if is_binary_file(filepath):
                    continue
                
                file_count += 1
                
                yield FileInfo(
                    path=filepath,
                    relative_path=str(filepath.relative_to(root)),
                    size=stat.st_size,
                    modified_time=stat.st_mtime,
                    extension=ext,
                    is_test=is_test_file(filepath),
                )
                
            except (OSError, IOError):
                # Skip files we can't stat
                continue


def filter_files(
    files: list[FileInfo],
    config: Config,
) -> list[FileInfo]:
    """Filter files based on configuration.
    
    Args:
        files: List of FileInfo objects
        config: Configuration with filter settings
        
    Returns:
        Filtered list of FileInfo
    """
    result = files.copy()
    
    # Filter out test files if configured
    if config.exclude_tests:
        result = [f for f in result if not f.is_test]
    
    return result
