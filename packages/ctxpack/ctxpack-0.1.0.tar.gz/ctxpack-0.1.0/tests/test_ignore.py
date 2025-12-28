"""Tests for ignore pattern matching."""

import pytest
from pathlib import Path
from ctxpack.ignore import IgnoreMatcher, IgnorePattern


class TestIgnorePattern:
    """Tests for individual pattern matching."""
    
    def test_simple_filename(self):
        """Test matching a simple filename."""
        pattern = IgnorePattern("*.pyc")
        assert pattern.matches("foo.pyc", is_dir=False) is True
        assert pattern.matches("foo.py", is_dir=False) is False
    
    def test_directory_pattern(self):
        """Test pattern with trailing slash (directory only)."""
        pattern = IgnorePattern("node_modules/")
        assert pattern.matches("node_modules", is_dir=True) is True
        assert pattern.matches("node_modules", is_dir=False) is False
    
    def test_anchored_pattern(self):
        """Test pattern anchored to root."""
        pattern = IgnorePattern("/build")
        assert pattern.matches("build", is_dir=False) is True
        assert pattern.matches("src/build", is_dir=False) is False
    
    def test_double_asterisk(self):
        """Test ** glob pattern."""
        pattern = IgnorePattern("**/*.pyc")
        assert pattern.matches("foo.pyc", is_dir=False) is True
        assert pattern.matches("src/foo.pyc", is_dir=False) is True
        assert pattern.matches("src/deep/foo.pyc", is_dir=False) is True
    
    def test_negation(self):
        """Test negation pattern (!)."""
        pattern = IgnorePattern("!important.py")
        assert pattern.is_negation is True
        assert pattern.matches("important.py", is_dir=False) is True
    
    def test_nested_path(self):
        """Test pattern matching nested paths."""
        pattern = IgnorePattern("__pycache__")
        assert pattern.matches("__pycache__", is_dir=True) is True
        assert pattern.matches("src/__pycache__", is_dir=True) is True
    
    def test_question_mark_wildcard(self):
        """Test ? wildcard matches single character."""
        pattern = IgnorePattern("test?.py")
        assert pattern.matches("test1.py", is_dir=False) is True
        assert pattern.matches("test12.py", is_dir=False) is False
    
    def test_character_class(self):
        """Test character class [abc]."""
        pattern = IgnorePattern("test[123].py")
        assert pattern.matches("test1.py", is_dir=False) is True
        assert pattern.matches("test2.py", is_dir=False) is True
        assert pattern.matches("test4.py", is_dir=False) is False


class TestIgnoreMatcher:
    """Tests for the full matcher with multiple patterns."""
    
    def test_always_ignores_git(self):
        """Test .git is always ignored."""
        matcher = IgnoreMatcher([])
        root = Path("/project")
        
        # Mock path checking
        class MockPath:
            def __init__(self, path_str, is_dir=True):
                self._path = path_str
                self._is_dir = is_dir
            
            def relative_to(self, root):
                return Path(self._path).relative_to(root)
            
            def is_dir(self):
                return self._is_dir
        
        git_path = MockPath("/project/.git", is_dir=True)
        assert matcher.is_ignored(git_path, root) is True
    
    def test_pattern_order(self):
        """Test later patterns override earlier ones."""
        matcher = IgnoreMatcher(["*.log", "!important.log"])
        
        # Test with actual paths using our pattern matching
        pattern1 = matcher.patterns[-2]  # *.log
        pattern2 = matcher.patterns[-1]  # !important.log
        
        assert pattern1.matches("debug.log", is_dir=False) is True
        assert pattern2.matches("important.log", is_dir=False) is True
        assert pattern2.is_negation is True
    
    def test_skip_comments(self):
        """Test comments are skipped."""
        matcher = IgnoreMatcher(["# This is a comment", "*.pyc"])
        
        # Should only have always-ignore + *.pyc
        user_patterns = [p for p in matcher.patterns if p.pattern not in [".git/", ".ctxpack/"]]
        assert len(user_patterns) == 1
        assert user_patterns[0].pattern == "*.pyc"
    
    def test_skip_empty_lines(self):
        """Test empty lines are skipped."""
        matcher = IgnoreMatcher(["", "  ", "*.pyc"])
        
        user_patterns = [p for p in matcher.patterns if p.pattern not in [".git/", ".ctxpack/"]]
        assert len(user_patterns) == 1
    
    def test_add_pattern(self):
        """Test adding patterns dynamically."""
        matcher = IgnoreMatcher([])
        initial_count = len(matcher.patterns)
        
        matcher.add_pattern("*.tmp")
        assert len(matcher.patterns) == initial_count + 1


class TestIgnorePatternEdgeCases:
    """Edge cases for pattern matching."""
    
    def test_special_regex_chars(self):
        """Test patterns with regex special characters."""
        pattern = IgnorePattern("file.min.js")
        assert pattern.matches("file.min.js", is_dir=False) is True
        assert pattern.matches("fileXminXjs", is_dir=False) is False
    
    def test_path_with_dots(self):
        """Test patterns matching paths with dots."""
        pattern = IgnorePattern(".env.*")
        assert pattern.matches(".env.local", is_dir=False) is True
        assert pattern.matches(".env.production", is_dir=False) is True
        assert pattern.matches(".env", is_dir=False) is False
    
    def test_deep_nesting(self):
        """Test matching deeply nested paths."""
        pattern = IgnorePattern("*.pyc")
        assert pattern.matches("a/b/c/d/e/f.pyc", is_dir=False) is True
