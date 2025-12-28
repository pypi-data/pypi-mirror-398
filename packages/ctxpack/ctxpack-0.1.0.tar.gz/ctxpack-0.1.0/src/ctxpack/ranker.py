"""File ranking and selection for ctxpack."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ctxpack.config import Config
from ctxpack.graph import ImportGraph
from ctxpack.scanner import FileInfo


@dataclass
class ScoredFile:
    """A file with its calculated score and breakdown."""
    
    file_info: FileInfo
    score: float
    score_breakdown: dict[str, float]
    reason: str
    
    @property
    def path(self) -> str:
        return self.file_info.relative_path


def calculate_recency_score(file_info: FileInfo, max_age_hours: float = 168.0) -> float:
    """Calculate recency score (higher = more recent).
    
    Args:
        file_info: File information
        max_age_hours: Max age to consider (default: 1 week)
        
    Returns:
        Score between 0.0 and 1.0
    """
    age = file_info.age_hours
    if age >= max_age_hours:
        return 0.0
    return 1.0 - (age / max_age_hours)


def calculate_size_score(file_info: FileInfo, max_size: int = 50_000) -> float:
    """Calculate size score (higher = smaller file).
    
    Smaller files are often more relevant (config, main entry points).
    
    Args:
        file_info: File information
        max_size: Max size to consider (default: 50KB)
        
    Returns:
        Score between 0.0 and 1.0
    """
    size = file_info.size
    if size >= max_size:
        return 0.0
    return 1.0 - (size / max_size)


def rank_files_simple(
    files: list[FileInfo],
    config: Config,
) -> list[ScoredFile]:
    """Rank files using simple mode (recency + size).
    
    Args:
        files: List of FileInfo objects
        config: Configuration with scoring weights
        
    Returns:
        List of ScoredFile sorted by score descending
    """
    scored = []
    
    for file_info in files:
        recency = calculate_recency_score(file_info)
        size = calculate_size_score(file_info)
        
        score = (
            config.recency_weight * recency +
            config.size_weight * size
        )
        
        breakdown = {
            "recency": recency,
            "size": size,
        }
        
        # Generate reason string
        reasons = []
        if recency > 0.7:
            reasons.append("recently modified")
        elif recency > 0.3:
            reasons.append("modified this week")
        if size > 0.7:
            reasons.append("small file")
        
        reason = ", ".join(reasons) if reasons else "standard"
        
        scored.append(ScoredFile(
            file_info=file_info,
            score=score,
            score_breakdown=breakdown,
            reason=reason,
        ))
    
    # Sort by score descending
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


def rank_files_smart(
    files: list[FileInfo],
    config: Config,
    graph: ImportGraph,
) -> list[ScoredFile]:
    """Rank files using smart mode (adds import graph boost).
    
    Args:
        files: List of FileInfo objects
        config: Configuration with scoring settings
        graph: Import relationship graph
        
    Returns:
        List of ScoredFile sorted by score descending
    """
    # Start with simple scoring
    scored = rank_files_simple(files, config)
    
    # Add graph-based boosts
    for sf in scored:
        rel_path = sf.file_info.relative_path.replace("\\", "/")
        
        import_count = graph.get_import_count(rel_path)
        imported_by_count = graph.get_imported_by_count(rel_path)
        
        import_boost = config.import_boost * min(import_count, 10)  # Cap at 10
        ref_boost = config.reference_boost * min(imported_by_count, 20)  # Cap at 20
        
        sf.score += import_boost + ref_boost
        sf.score_breakdown["imports"] = import_count
        sf.score_breakdown["imported_by"] = imported_by_count
        sf.score_breakdown["import_boost"] = import_boost
        sf.score_breakdown["ref_boost"] = ref_boost
        
        # Update reason
        if imported_by_count >= 5:
            sf.reason += f", core file (imported by {imported_by_count})"
        elif imported_by_count >= 2:
            sf.reason += f", used by {imported_by_count} files"
    
    # Re-sort by updated scores
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


def select_top_files(
    scored_files: list[ScoredFile],
    max_files: int,
    max_bytes: int,
) -> list[ScoredFile]:
    """Select top files within limits.
    
    Args:
        scored_files: Sorted list of ScoredFile
        max_files: Maximum number of files
        max_bytes: Maximum total bytes
        
    Returns:
        Selected files within limits
    """
    selected = []
    total_bytes = 0
    
    for sf in scored_files:
        if len(selected) >= max_files:
            break
        
        file_size = sf.file_info.size
        if total_bytes + file_size > max_bytes:
            # Skip this file but continue looking for smaller ones
            continue
        
        selected.append(sf)
        total_bytes += file_size
    
    return selected
