"""Utility functions for ctxpack."""

from __future__ import annotations

import os
from pathlib import Path

# Extension to language mapping for syntax highlighting
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".txt": "text",
    ".dockerfile": "dockerfile",
    ".vue": "vue",
    ".svelte": "svelte",
}


def get_language_for_extension(ext: str) -> str:
    """Get the language identifier for syntax highlighting based on file extension.
    
    Args:
        ext: File extension including the dot (e.g., '.py')
        
    Returns:
        Language identifier for markdown code blocks
    """
    return EXTENSION_LANGUAGE_MAP.get(ext.lower(), "text")


def format_bytes(size: int) -> str:
    """Format byte size to human-readable string.
    
    Args:
        size: Size in bytes
        
    Returns:
        Human-readable size string (e.g., '1.5 KB')
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def is_binary_file(path: Path, sample_size: int = 8192) -> bool:
    """Detect if a file is binary by checking for null bytes.
    
    Args:
        path: Path to the file
        sample_size: Number of bytes to sample from the beginning
        
    Returns:
        True if file appears to be binary
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample_size)
            # Check for null bytes - strong indicator of binary
            if b"\x00" in chunk:
                return True
            # Check for high ratio of non-text bytes
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            if len(chunk) > 0 and non_text / len(chunk) > 0.30:
                return True
        return False
    except (OSError, IOError):
        return True


def safe_read_file(path: Path) -> str | None:
    """Safely read a file with encoding fallback.
    
    Args:
        path: Path to the file
        
    Returns:
        File contents as string, or None if unreadable
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    
    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except (OSError, IOError):
            return None
    
    return None


def is_test_file(path: Path) -> bool:
    """Detect if a file is a test file based on naming conventions.
    
    Args:
        path: Path to the file
        
    Returns:
        True if file appears to be a test file
    """
    name = path.name.lower()
    parts = [p.lower() for p in path.parts]
    
    # Check filename patterns
    test_patterns = [
        name.startswith("test_"),
        name.endswith("_test.py"),
        name.endswith(".test.js"),
        name.endswith(".test.ts"),
        name.endswith(".test.jsx"),
        name.endswith(".test.tsx"),
        name.endswith(".spec.js"),
        name.endswith(".spec.ts"),
        name.endswith(".spec.jsx"),
        name.endswith(".spec.tsx"),
        name == "conftest.py",
    ]
    
    # Check directory patterns
    test_dirs = ["test", "tests", "__tests__", "spec", "specs"]
    dir_match = any(d in parts for d in test_dirs)
    
    return any(test_patterns) or dir_match


def get_project_name(path: Path) -> str:
    """Get project name from path, preferring common config files.
    
    Args:
        path: Root path of the project
        
    Returns:
        Project name string
    """
    # Try common project files
    for config_file in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod"]:
        config_path = path / config_file
        if config_path.exists():
            try:
                content = safe_read_file(config_path)
                if content:
                    # Simple extraction - just get the name field
                    if config_file == "package.json":
                        import json
                        data = json.loads(content)
                        if "name" in data:
                            return data["name"]
                    elif "name" in content:
                        # Basic TOML parsing for name
                        for line in content.split("\n"):
                            if line.strip().startswith("name"):
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    return parts[1].strip().strip('"\'')
            except Exception:
                pass
    
    # Fall back to directory name
    return path.resolve().name
