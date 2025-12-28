"""Markdown output generation for ctxpack."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ctxpack.config import Config
from ctxpack.ranker import ScoredFile
from ctxpack.utils import format_bytes, get_language_for_extension, get_project_name, safe_read_file


def generate_markdown(
    root: Path,
    selected_files: list[ScoredFile],
    total_scanned: int,
    config: Config,
    verbose: bool = False,
) -> str:
    """Generate Markdown context package.
    
    Args:
        root: Project root directory
        selected_files: List of selected files with scores
        total_scanned: Total files scanned
        config: Configuration used
        verbose: Include detailed scoring information
        
    Returns:
        Markdown string
    """
    lines: list[str] = []
    
    # Header
    project_name = get_project_name(root)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    total_size = sum(sf.file_info.size for sf in selected_files)
    
    lines.append(f"# Context Package: {project_name}")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Mode:** {config.mode}")
    lines.append(f"**Files scanned:** {total_scanned}")
    lines.append(f"**Files selected:** {len(selected_files)}")
    lines.append(f"**Total size:** {format_bytes(total_size)}")
    lines.append("")
    
    # Selection rationale table
    if selected_files:
        lines.append("## Selection Rationale")
        lines.append("")
        
        if verbose:
            lines.append("| File | Score | Recency | Size | Reason |")
            lines.append("|------|-------|---------|------|--------|")
            for sf in selected_files:
                recency = sf.score_breakdown.get("recency", 0)
                size = sf.score_breakdown.get("size", 0)
                lines.append(
                    f"| `{sf.path}` | {sf.score:.2f} | {recency:.2f} | {size:.2f} | {sf.reason} |"
                )
        else:
            lines.append("| File | Score | Reason |")
            lines.append("|------|-------|--------|")
            for sf in selected_files:
                lines.append(f"| `{sf.path}` | {sf.score:.2f} | {sf.reason} |")
        
        lines.append("")
    
    # File contents
    lines.append("---")
    lines.append("")
    
    for sf in selected_files:
        file_path = sf.file_info.path
        rel_path = sf.path
        
        lines.append(f"## {rel_path}")
        lines.append("")
        
        # Read file content
        content = safe_read_file(file_path)
        if content is None:
            lines.append("*Unable to read file*")
            lines.append("")
            continue
        
        # Get language for syntax highlighting
        lang = get_language_for_extension(sf.file_info.extension)
        
        # Add fenced code block
        lines.append(f"```{lang}")
        # Ensure content doesn't end with extra newlines
        lines.append(content.rstrip())
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def write_output(
    markdown: str,
    output_path: Path | None = None,
) -> None:
    """Write markdown output to file or stdout.
    
    Args:
        markdown: Markdown content
        output_path: Output file path (None for stdout)
    """
    if output_path is None:
        print(markdown)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
