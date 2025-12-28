"""Import/reference graph building for smart mode."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ctxpack.scanner import FileInfo
from ctxpack.utils import safe_read_file


@dataclass
class ImportGraph:
    """Graph of import/reference relationships between files."""
    
    # file path -> list of files it imports
    imports: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    
    # file path -> list of files that import it
    imported_by: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    
    def get_import_count(self, path: str) -> int:
        """Get number of files this file imports."""
        return len(self.imports.get(path, []))
    
    def get_imported_by_count(self, path: str) -> int:
        """Get number of files that import this file."""
        return len(self.imported_by.get(path, []))


# Python import patterns
PYTHON_IMPORT_RE = re.compile(
    r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))',
    re.MULTILINE
)

# JavaScript/TypeScript import patterns
JS_IMPORT_RE = re.compile(
    r'''(?:import\s+.*?\s+from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))''',
    re.MULTILINE
)


def parse_python_imports(content: str) -> list[str]:
    """Extract import module names from Python source.
    
    Args:
        content: Python source code
        
    Returns:
        List of imported module names
    """
    imports = []
    for match in PYTHON_IMPORT_RE.finditer(content):
        module = match.group(1) or match.group(2)
        if module:
            # Get the top-level module name
            top_module = module.split(".")[0]
            imports.append(top_module)
    return imports


def parse_js_imports(content: str) -> list[str]:
    """Extract import paths from JavaScript/TypeScript source.
    
    Args:
        content: JS/TS source code
        
    Returns:
        List of imported paths
    """
    imports = []
    for match in JS_IMPORT_RE.finditer(content):
        path = match.group(1) or match.group(2)
        if path:
            # Only consider relative imports
            if path.startswith("."):
                imports.append(path)
    return imports


def resolve_python_import(
    importing_file: Path,
    module_name: str,
    project_root: Path,
    all_files: set[str],
) -> str | None:
    """Resolve a Python import to a file path.
    
    Args:
        importing_file: Path of the file doing the import
        module_name: Module name being imported
        project_root: Project root directory
        all_files: Set of relative paths of all files
        
    Returns:
        Resolved relative path or None
    """
    # Try as a direct file
    candidates = [
        f"{module_name}.py",
        f"{module_name}/__init__.py",
        str(importing_file.parent.relative_to(project_root) / f"{module_name}.py"),
    ]
    
    for candidate in candidates:
        normalized = candidate.replace(os.sep, "/")
        if normalized in all_files:
            return normalized
    
    return None


def resolve_js_import(
    importing_file: Path,
    import_path: str,
    project_root: Path,
    all_files: set[str],
) -> str | None:
    """Resolve a JS/TS import to a file path.
    
    Args:
        importing_file: Path of the file doing the import
        import_path: Import path (e.g., './utils')
        project_root: Project root directory
        all_files: Set of relative paths of all files
        
    Returns:
        Resolved relative path or None
    """
    # Resolve relative to importing file's directory
    importing_dir = importing_file.parent
    resolved = (importing_dir / import_path).resolve()
    
    try:
        rel_path = resolved.relative_to(project_root)
    except ValueError:
        return None
    
    rel_str = str(rel_path).replace(os.sep, "/")
    
    # Try with various extensions
    extensions = [".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"]
    
    # Check exact match first
    if rel_str in all_files:
        return rel_str
    
    # Try with extensions
    for ext in extensions:
        candidate = rel_str + ext
        if candidate in all_files:
            return candidate
    
    return None


def build_import_graph(
    files: list[FileInfo],
    project_root: Path,
) -> ImportGraph:
    """Build import/reference graph from file list.
    
    Args:
        files: List of FileInfo objects
        project_root: Project root directory
        
    Returns:
        ImportGraph instance
    """
    graph = ImportGraph()
    all_files = {f.relative_path.replace(os.sep, "/") for f in files}
    file_by_path = {f.relative_path.replace(os.sep, "/"): f for f in files}
    
    for file_info in files:
        content = safe_read_file(file_info.path)
        if content is None:
            continue
        
        rel_path = file_info.relative_path.replace(os.sep, "/")
        ext = file_info.extension.lower()
        
        # Parse imports based on language
        if ext in (".py", ".pyi"):
            imports = parse_python_imports(content)
            for module in imports:
                resolved = resolve_python_import(
                    file_info.path, module, project_root, all_files
                )
                if resolved and resolved != rel_path:
                    graph.imports[rel_path].append(resolved)
                    graph.imported_by[resolved].append(rel_path)
        
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            imports = parse_js_imports(content)
            for import_path in imports:
                resolved = resolve_js_import(
                    file_info.path, import_path, project_root, all_files
                )
                if resolved and resolved != rel_path:
                    graph.imports[rel_path].append(resolved)
                    graph.imported_by[resolved].append(rel_path)
    
    return graph
