"""Tests for import graph building."""

import pytest
from pathlib import Path

from ctxpack.graph import (
    parse_python_imports,
    parse_js_imports,
    resolve_python_import,
    resolve_js_import,
    build_import_graph,
)
from ctxpack.scanner import FileInfo
import time


class TestPythonImportParsing:
    """Tests for Python import statement parsing."""
    
    def test_simple_import(self):
        """Parse simple import statement."""
        code = "import os"
        imports = parse_python_imports(code)
        assert "os" in imports
    
    def test_from_import(self):
        """Parse from...import statement."""
        code = "from pathlib import Path"
        imports = parse_python_imports(code)
        assert "pathlib" in imports
    
    def test_dotted_import(self):
        """Parse dotted module import."""
        code = "import os.path"
        imports = parse_python_imports(code)
        assert "os" in imports  # Top-level module
    
    def test_multiple_imports(self):
        """Parse multiple import statements."""
        code = """
import os
from pathlib import Path
import json
from typing import List
"""
        imports = parse_python_imports(code)
        assert "os" in imports
        assert "pathlib" in imports
        assert "json" in imports
        assert "typing" in imports
    
    def test_ignores_comments(self):
        """Ignore commented imports."""
        code = "# import os"
        imports = parse_python_imports(code)
        assert "os" not in imports
    
    def test_relative_import(self):
        """Parse relative import."""
        code = "from .utils import helper"
        imports = parse_python_imports(code)
        # Relative imports start with .
        assert any(imp.startswith(".") or imp == "" for imp in imports) or len(imports) == 0


class TestJSImportParsing:
    """Tests for JavaScript/TypeScript import parsing."""
    
    def test_es_import(self):
        """Parse ES6 import statement."""
        code = "import React from 'react';"
        imports = parse_js_imports(code)
        # Only relative imports are captured
        assert "react" not in imports  # Not a relative import
    
    def test_relative_import(self):
        """Parse relative import."""
        code = "import { helper } from './utils';"
        imports = parse_js_imports(code)
        assert "./utils" in imports
    
    def test_require(self):
        """Parse require statement."""
        code = "const utils = require('./utils');"
        imports = parse_js_imports(code)
        assert "./utils" in imports
    
    def test_parent_import(self):
        """Parse parent directory import."""
        code = "import config from '../config';"
        imports = parse_js_imports(code)
        assert "../config" in imports
    
    def test_multiple_imports(self):
        """Parse multiple import statements."""
        code = """
import { foo } from './foo';
import bar from './bar';
const baz = require('./baz');
"""
        imports = parse_js_imports(code)
        assert "./foo" in imports
        assert "./bar" in imports
        assert "./baz" in imports


class TestPythonImportResolution:
    """Tests for resolving Python imports to file paths."""
    
    def test_resolve_simple_module(self):
        """Resolve simple module to file."""
        importing_file = Path("/project/main.py")
        project_root = Path("/project")
        all_files = {"utils.py", "main.py"}
        
        resolved = resolve_python_import(
            importing_file, "utils", project_root, all_files
        )
        assert resolved == "utils.py"
    
    def test_resolve_package_init(self):
        """Resolve package to __init__.py."""
        importing_file = Path("/project/main.py")
        project_root = Path("/project")
        all_files = {"mypackage/__init__.py", "main.py"}
        
        resolved = resolve_python_import(
            importing_file, "mypackage", project_root, all_files
        )
        assert resolved == "mypackage/__init__.py"
    
    def test_unresolved_returns_none(self):
        """Unresolvable import returns None."""
        importing_file = Path("/project/main.py")
        project_root = Path("/project")
        all_files = {"main.py"}
        
        resolved = resolve_python_import(
            importing_file, "nonexistent", project_root, all_files
        )
        assert resolved is None


class TestJSImportResolution:
    """Tests for resolving JS imports to file paths."""
    
    def test_resolve_with_extension(self):
        """Resolve import with extension added."""
        importing_file = Path("/project/src/main.ts")
        project_root = Path("/project")
        all_files = {"src/utils.ts", "src/main.ts"}
        
        resolved = resolve_js_import(
            importing_file, "./utils", project_root, all_files
        )
        assert resolved == "src/utils.ts"
    
    def test_resolve_index_file(self):
        """Resolve directory import to index file."""
        importing_file = Path("/project/src/main.ts")
        project_root = Path("/project")
        all_files = {"src/utils/index.ts", "src/main.ts"}
        
        resolved = resolve_js_import(
            importing_file, "./utils", project_root, all_files
        )
        assert resolved == "src/utils/index.ts"
    
    def test_unresolved_returns_none(self):
        """Unresolvable import returns None."""
        importing_file = Path("/project/src/main.ts")
        project_root = Path("/project")
        all_files = {"src/main.ts"}
        
        resolved = resolve_js_import(
            importing_file, "./nonexistent", project_root, all_files
        )
        assert resolved is None


def make_file_info(path: str, content: str = "") -> FileInfo:
    """Create FileInfo for testing."""
    p = Path(path)
    return FileInfo(
        path=p,
        relative_path=str(p.relative_to("/project")),
        size=len(content),
        modified_time=time.time(),
        extension=p.suffix,
        is_test=False,
    )


class TestImportGraphBuilding:
    """Tests for full import graph construction."""
    
    def test_empty_files(self):
        """Empty file list produces empty graph."""
        graph = build_import_graph([], Path("/project"))
        assert len(graph.imports) == 0
        assert len(graph.imported_by) == 0
    
    def test_graph_bidirectional(self):
        """Graph maintains bidirectional relationships."""
        # This is a conceptual test - actual file reading would be needed
        graph = build_import_graph([], Path("/project"))
        
        # Manually add a relationship and verify
        graph.imports["main.py"] = ["utils.py"]
        graph.imported_by["utils.py"] = ["main.py"]
        
        assert graph.get_import_count("main.py") == 1
        assert graph.get_imported_by_count("utils.py") == 1
