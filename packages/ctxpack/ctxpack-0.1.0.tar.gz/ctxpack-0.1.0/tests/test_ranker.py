"""Tests for file ranking and selection."""

import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from ctxpack.config import Config
from ctxpack.graph import ImportGraph
from ctxpack.ranker import (
    ScoredFile,
    calculate_recency_score,
    calculate_size_score,
    rank_files_simple,
    rank_files_smart,
    select_top_files,
)
from ctxpack.scanner import FileInfo


def make_file_info(
    name: str,
    size: int = 1000,
    age_hours: float = 1.0,
    is_test: bool = False,
) -> FileInfo:
    """Create a FileInfo for testing."""
    return FileInfo(
        path=Path(f"/project/{name}"),
        relative_path=name,
        size=size,
        modified_time=time.time() - (age_hours * 3600),
        extension=Path(name).suffix,
        is_test=is_test,
    )


class TestRecencyScore:
    """Tests for recency scoring."""
    
    def test_recent_file_high_score(self):
        """Recently modified files get high scores."""
        file = make_file_info("main.py", age_hours=1.0)
        score = calculate_recency_score(file, max_age_hours=168.0)
        assert score > 0.9
    
    def test_old_file_low_score(self):
        """Old files get low scores."""
        file = make_file_info("main.py", age_hours=150.0)
        score = calculate_recency_score(file, max_age_hours=168.0)
        assert score < 0.2
    
    def test_very_old_file_zero_score(self):
        """Files older than max get zero."""
        file = make_file_info("main.py", age_hours=200.0)
        score = calculate_recency_score(file, max_age_hours=168.0)
        assert score == 0.0


class TestSizeScore:
    """Tests for size scoring."""
    
    def test_small_file_high_score(self):
        """Small files get high scores."""
        file = make_file_info("main.py", size=500)
        score = calculate_size_score(file, max_size=50000)
        assert score > 0.9
    
    def test_large_file_low_score(self):
        """Large files get low scores."""
        file = make_file_info("main.py", size=40000)
        score = calculate_size_score(file, max_size=50000)
        assert score < 0.3
    
    def test_huge_file_zero_score(self):
        """Files larger than max get zero."""
        file = make_file_info("main.py", size=60000)
        score = calculate_size_score(file, max_size=50000)
        assert score == 0.0


class TestSimpleRanking:
    """Tests for simple mode ranking."""
    
    def test_ranks_by_combined_score(self):
        """Files are ranked by combined recency and size score."""
        files = [
            make_file_info("old_large.py", size=30000, age_hours=100),
            make_file_info("new_small.py", size=500, age_hours=1),
            make_file_info("medium.py", size=10000, age_hours=50),
        ]
        
        config = Config()
        scored = rank_files_simple(files, config)
        
        # new_small should be first (recent + small)
        assert scored[0].path == "new_small.py"
        # old_large should be last
        assert scored[-1].path == "old_large.py"
    
    def test_includes_score_breakdown(self):
        """Scored files include breakdown."""
        files = [make_file_info("main.py")]
        config = Config()
        scored = rank_files_simple(files, config)
        
        assert "recency" in scored[0].score_breakdown
        assert "size" in scored[0].score_breakdown
    
    def test_generates_reason(self):
        """Scored files include human-readable reason."""
        files = [make_file_info("main.py", size=100, age_hours=0.5)]
        config = Config()
        scored = rank_files_simple(files, config)
        
        assert scored[0].reason != ""


class TestSmartRanking:
    """Tests for smart mode ranking."""
    
    def test_boosts_imported_files(self):
        """Files imported by many others get boosted."""
        files = [
            make_file_info("utils.py", size=1000, age_hours=50),
            make_file_info("main.py", size=1000, age_hours=50),
        ]
        
        # utils.py is imported by main.py
        graph = ImportGraph()
        graph.imports["main.py"] = ["utils.py"]
        graph.imported_by["utils.py"] = ["main.py"]
        
        config = Config()
        scored = rank_files_smart(files, config, graph)
        
        # Find utils.py score
        utils_score = next(s for s in scored if s.path == "utils.py")
        main_score = next(s for s in scored if s.path == "main.py")
        
        # utils.py should have reference boost
        assert utils_score.score_breakdown.get("ref_boost", 0) > 0
    
    def test_heavily_imported_file_ranks_higher(self):
        """A core utility file imported by many should rank high."""
        files = [
            make_file_info("utils.py", size=5000, age_hours=100),  # Old, medium
            make_file_info("random.py", size=1000, age_hours=1),   # New, small
        ]
        
        # utils.py is imported by 10 files
        graph = ImportGraph()
        graph.imported_by["utils.py"] = [f"file{i}.py" for i in range(10)]
        
        config = Config(reference_boost=0.15)
        scored = rank_files_smart(files, config, graph)
        
        # utils.py should be first despite being older/larger
        assert scored[0].path == "utils.py"


class TestFileSelection:
    """Tests for selecting files within limits."""
    
    def test_respects_max_files(self):
        """Selection respects max files limit."""
        scored = [
            ScoredFile(make_file_info(f"file{i}.py"), 1.0 - i * 0.1, {}, "test")
            for i in range(10)
        ]
        
        selected = select_top_files(scored, max_files=5, max_bytes=1000000)
        assert len(selected) == 5
    
    def test_respects_max_bytes(self):
        """Selection respects max bytes limit."""
        scored = [
            ScoredFile(make_file_info(f"file{i}.py", size=1000), 1.0, {}, "test")
            for i in range(10)
        ]
        
        selected = select_top_files(scored, max_files=100, max_bytes=5000)
        assert len(selected) == 5  # 5 files * 1000 bytes = 5000
    
    def test_skips_large_files_for_smaller_ones(self):
        """Selection skips large files to include smaller ones within byte limit."""
        scored = [
            ScoredFile(make_file_info("big.py", size=8000), 1.0, {}, "high score"),
            ScoredFile(make_file_info("small1.py", size=3000), 0.9, {}, "medium"),
            ScoredFile(make_file_info("small2.py", size=3000), 0.8, {}, "medium"),
        ]
        
        # With 7000 byte limit, should skip big.py and get both small files
        selected = select_top_files(scored, max_files=10, max_bytes=7000)
        
        paths = [s.path for s in selected]
        assert "big.py" not in paths
        assert "small1.py" in paths
        assert "small2.py" in paths
