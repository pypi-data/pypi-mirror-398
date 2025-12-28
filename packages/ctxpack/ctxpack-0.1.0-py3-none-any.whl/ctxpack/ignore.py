"""Gitignore-style pattern matching for ctxpack."""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IgnorePattern:
    """A single ignore pattern with metadata."""
    
    pattern: str
    is_negation: bool = False
    is_dir_only: bool = False
    is_anchored: bool = False
    regex: re.Pattern | None = field(default=None, repr=False)
    
    def __post_init__(self) -> None:
        """Compile the pattern to regex."""
        self.regex = self._compile_pattern()
    
    def _compile_pattern(self) -> re.Pattern:
        """Convert gitignore pattern to regex."""
        pattern = self.pattern
        
        # Handle directory-only patterns (trailing /)
        if pattern.endswith("/"):
            pattern = pattern[:-1]
            self.is_dir_only = True
        
        # Handle negation
        if pattern.startswith("!"):
            pattern = pattern[1:]
            self.is_negation = True
        
        # Handle anchored patterns (starting with / or containing /)
        if pattern.startswith("/"):
            pattern = pattern[1:]
            self.is_anchored = True
        elif "/" in pattern and not pattern.startswith("**/"):
            self.is_anchored = True
        
        # Convert gitignore glob to regex
        regex_pattern = self._glob_to_regex(pattern)
        
        return re.compile(regex_pattern)
    
    def _glob_to_regex(self, pattern: str) -> str:
        """Convert a gitignore glob pattern to regex.
        
        Args:
            pattern: Gitignore-style pattern
            
        Returns:
            Regex pattern string
        """
        # Escape special regex chars except glob chars
        i = 0
        n = len(pattern)
        result = []
        
        while i < n:
            c = pattern[i]
            if c == "*":
                if i + 1 < n and pattern[i + 1] == "*":
                    # ** matches everything including /
                    if i + 2 < n and pattern[i + 2] == "/":
                        result.append("(?:.*/)?")
                        i += 3
                        continue
                    else:
                        result.append(".*")
                        i += 2
                        continue
                else:
                    # * matches everything except /
                    result.append("[^/]*")
            elif c == "?":
                result.append("[^/]")
            elif c == "[":
                # Character class
                j = i + 1
                if j < n and pattern[j] == "!":
                    j += 1
                if j < n and pattern[j] == "]":
                    j += 1
                while j < n and pattern[j] != "]":
                    j += 1
                if j >= n:
                    result.append("\\[")
                else:
                    stuff = pattern[i + 1:j]
                    if stuff.startswith("!"):
                        stuff = "^" + stuff[1:]
                    elif stuff.startswith("^"):
                        stuff = "\\" + stuff
                    result.append(f"[{stuff}]")
                    i = j
            elif c in ".^$+{}\\|()":
                result.append("\\" + c)
            else:
                result.append(c)
            i += 1
        
        return "^" + "".join(result) + "$"
    
    def matches(self, path: str, is_dir: bool = False) -> bool:
        """Check if the path matches this pattern.
        
        Args:
            path: Relative path to check (using / separators)
            is_dir: Whether the path is a directory
            
        Returns:
            True if path matches
        """
        if self.is_dir_only and not is_dir:
            return False
        
        if self.regex is None:
            return False
        
        # For anchored patterns, match from root
        if self.is_anchored:
            return bool(self.regex.match(path))
        
        # For non-anchored patterns, try matching at any level
        parts = path.split("/")
        for i in range(len(parts)):
            subpath = "/".join(parts[i:])
            if self.regex.match(subpath):
                return True
        
        return False


class IgnoreMatcher:
    """Matches paths against gitignore-style patterns."""
    
    # Always ignored, regardless of .ctxpackignore
    ALWAYS_IGNORE = [".git/", ".ctxpack/"]
    
    def __init__(self, patterns: list[str] | None = None) -> None:
        """Initialize the matcher with patterns.
        
        Args:
            patterns: List of gitignore-style patterns
        """
        self.patterns: list[IgnorePattern] = []
        
        # Add always-ignore patterns first
        for p in self.ALWAYS_IGNORE:
            self.patterns.append(IgnorePattern(p))
        
        # Add user patterns
        if patterns:
            for p in patterns:
                p = p.strip()
                if p and not p.startswith("#"):
                    self.patterns.append(IgnorePattern(p))
    
    @classmethod
    def from_file(cls, path: Path) -> IgnoreMatcher:
        """Load patterns from an ignore file.
        
        Args:
            path: Path to ignore file
            
        Returns:
            IgnoreMatcher instance
        """
        patterns = []
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    patterns = f.read().splitlines()
            except (OSError, IOError):
                pass
        return cls(patterns)
    
    @classmethod
    def from_directory(cls, directory: Path) -> IgnoreMatcher:
        """Load .ctxpackignore from a directory.
        
        Args:
            directory: Directory to search for .ctxpackignore
            
        Returns:
            IgnoreMatcher instance
        """
        ignore_file = directory / ".ctxpackignore"
        return cls.from_file(ignore_file)
    
    def is_ignored(self, path: Path, root: Path) -> bool:
        """Check if a path should be ignored.
        
        Args:
            path: Absolute path to check
            root: Root directory for relative path calculation
            
        Returns:
            True if path should be ignored
        """
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            return False
        
        # Normalize to forward slashes
        rel_str = str(rel_path).replace(os.sep, "/")
        is_dir = path.is_dir()
        
        # Check patterns in order (later patterns can override earlier ones)
        ignored = False
        for pattern in self.patterns:
            if pattern.matches(rel_str, is_dir):
                if pattern.is_negation:
                    ignored = False
                else:
                    ignored = True
        
        return ignored
    
    def add_pattern(self, pattern: str) -> None:
        """Add a pattern to the matcher.
        
        Args:
            pattern: Gitignore-style pattern
        """
        pattern = pattern.strip()
        if pattern and not pattern.startswith("#"):
            self.patterns.append(IgnorePattern(pattern))
