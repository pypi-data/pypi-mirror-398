"""Tests for file scanning."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from ctxpack.config import Config
from ctxpack.ignore import IgnoreMatcher
from ctxpack.scanner import FileInfo, filter_files, scan_directory


class TestFileScanning:
    """Tests for directory scanning."""
    
    def test_finds_python_files(self, tmp_path):
        """Scanner finds Python files."""
        # Create test files
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher([])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        assert len(files) == 2
        names = {f.path.name for f in files}
        assert "main.py" in names
        assert "utils.py" in names
    
    def test_respects_extension_filter(self, tmp_path):
        """Scanner filters by extension."""
        (tmp_path / "main.py").write_text("python")
        (tmp_path / "style.css").write_text("css")
        (tmp_path / "script.js").write_text("js")
        
        config = Config(extensions=[".py", ".js"])
        matcher = IgnoreMatcher([])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        assert len(files) == 2
        names = {f.path.name for f in files}
        assert "main.py" in names
        assert "script.js" in names
        assert "style.css" not in names
    
    def test_respects_ignore_patterns(self, tmp_path):
        """Scanner respects ignore patterns."""
        (tmp_path / "main.py").write_text("main")
        (tmp_path / "temp.py").write_text("temp")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher(["temp.py"])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        assert len(files) == 1
        assert files[0].path.name == "main.py"
    
    def test_ignores_directories(self, tmp_path):
        """Scanner ignores entire directories."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("main")
        
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.py").write_text("package")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher(["node_modules/"])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        assert len(files) == 1
        assert files[0].path.name == "main.py"
    
    def test_skips_empty_files(self, tmp_path):
        """Scanner skips empty files."""
        (tmp_path / "empty.py").write_text("")
        (tmp_path / "nonempty.py").write_text("content")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher([])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        assert len(files) == 1
        assert files[0].path.name == "nonempty.py"
    
    def test_recursive_scanning(self, tmp_path):
        """Scanner works recursively."""
        (tmp_path / "root.py").write_text("root")
        
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.py").write_text("nested")
        
        deep = subdir / "deep"
        deep.mkdir()
        (deep / "very_nested.py").write_text("very nested")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher([])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        assert len(files) == 3
    
    def test_max_scan_limit(self, tmp_path):
        """Scanner respects max scan limit."""
        for i in range(20):
            (tmp_path / f"file{i}.py").write_text(f"content {i}")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher([])
        
        files = list(scan_directory(tmp_path, config, matcher, max_scan=5))
        
        assert len(files) == 5
    
    def test_detects_test_files(self, tmp_path):
        """Scanner detects test files."""
        (tmp_path / "main.py").write_text("main")
        (tmp_path / "test_main.py").write_text("test")
        (tmp_path / "main_test.py").write_text("test")
        
        config = Config(extensions=[".py"])
        matcher = IgnoreMatcher([])
        
        files = list(scan_directory(tmp_path, config, matcher))
        
        test_files = [f for f in files if f.is_test]
        non_test_files = [f for f in files if not f.is_test]
        
        assert len(test_files) == 2
        assert len(non_test_files) == 1


class TestFileFiltering:
    """Tests for file filtering."""
    
    def test_excludes_test_files(self):
        """Filter excludes test files when configured."""
        files = [
            FileInfo(
                path=Path("/project/main.py"),
                relative_path="main.py",
                size=100,
                modified_time=time.time(),
                extension=".py",
                is_test=False,
            ),
            FileInfo(
                path=Path("/project/test_main.py"),
                relative_path="test_main.py",
                size=100,
                modified_time=time.time(),
                extension=".py",
                is_test=True,
            ),
        ]
        
        config = Config(exclude_tests=True)
        filtered = filter_files(files, config)
        
        assert len(filtered) == 1
        assert filtered[0].path.name == "main.py"
    
    def test_includes_test_files(self):
        """Filter includes test files when configured."""
        files = [
            FileInfo(
                path=Path("/project/main.py"),
                relative_path="main.py",
                size=100,
                modified_time=time.time(),
                extension=".py",
                is_test=False,
            ),
            FileInfo(
                path=Path("/project/test_main.py"),
                relative_path="test_main.py",
                size=100,
                modified_time=time.time(),
                extension=".py",
                is_test=True,
            ),
        ]
        
        config = Config(exclude_tests=False)
        filtered = filter_files(files, config)
        
        assert len(filtered) == 2


class TestFileInfo:
    """Tests for FileInfo dataclass."""
    
    def test_age_hours_calculation(self):
        """FileInfo correctly calculates age in hours."""
        now = time.time()
        two_hours_ago = now - (2 * 3600)
        
        info = FileInfo(
            path=Path("/project/main.py"),
            relative_path="main.py",
            size=100,
            modified_time=two_hours_ago,
            extension=".py",
            is_test=False,
        )
        
        # Should be approximately 2 hours
        assert 1.9 < info.age_hours < 2.1
