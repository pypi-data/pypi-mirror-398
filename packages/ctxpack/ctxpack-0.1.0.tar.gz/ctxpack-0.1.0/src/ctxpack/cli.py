"""CLI commands for ctxpack."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ctxpack import __version__
from ctxpack.config import Config, init_ctxpack
from ctxpack.graph import build_import_graph
from ctxpack.ignore import IgnoreMatcher
from ctxpack.output import generate_markdown, write_output
from ctxpack.ranker import rank_files_simple, rank_files_smart, select_top_files
from ctxpack.scanner import FileInfo, filter_files, scan_directory
from ctxpack.watcher import FileWatcher

app = typer.Typer(
    name="ctxpack",
    help="Automatically gather project context for LLMs.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ctxpack version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """ctxpack - Automatically gather project context for LLMs."""
    pass


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to initialize (default: current directory)",
        ),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f",
            help="Overwrite existing configuration",
        ),
    ] = False,
) -> None:
    """Initialize ctxpack in a project directory.
    
    Creates a .ctxpack/ folder with configuration and a .ctxpackignore file.
    """
    directory = path.resolve()
    
    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise typer.Exit(1)
    
    if not directory.is_dir():
        console.print(f"[red]Error:[/red] Path is not a directory: {directory}")
        raise typer.Exit(1)
    
    success, message = init_ctxpack(directory, force=force)
    
    if success:
        console.print(Panel(
            f"[green]✓[/green] {message}\n\n"
            f"Created:\n"
            f"  • [cyan].ctxpack/config.toml[/cyan] - Configuration file\n"
            f"  • [cyan].ctxpackignore[/cyan] - Ignore patterns\n\n"
            f"Next steps:\n"
            f"  1. Review and edit [cyan].ctxpackignore[/cyan]\n"
            f"  2. Run [cyan]ctxpack pack[/cyan] to generate context",
            title="ctxpack initialized",
            border_style="green",
        ))
    else:
        console.print(f"[yellow]Warning:[/yellow] {message}")
        raise typer.Exit(1)


@app.command()
def pack(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to pack (default: current directory)",
        ),
    ] = Path("."),
    max_files: Annotated[
        Optional[int],
        typer.Option(
            "--max-files", "-n",
            help="Maximum number of files to include",
        ),
    ] = None,
    max_bytes: Annotated[
        Optional[int],
        typer.Option(
            "--max-bytes", "-b",
            help="Maximum total output size in bytes",
        ),
    ] = None,
    extensions: Annotated[
        Optional[str],
        typer.Option(
            "--extensions", "-e",
            help="Comma-separated file extensions (e.g., .py,.js,.ts)",
        ),
    ] = None,
    include_tests: Annotated[
        bool,
        typer.Option(
            "--include-tests",
            help="Include test files",
        ),
    ] = False,
    exclude_tests: Annotated[
        bool,
        typer.Option(
            "--exclude-tests",
            help="Exclude test files (default)",
        ),
    ] = False,
    mode: Annotated[
        Optional[str],
        typer.Option(
            "--mode", "-m",
            help="Selection mode: simple or smart",
        ),
    ] = None,
    out: Annotated[
        Optional[Path],
        typer.Option(
            "--out", "-o",
            help="Output file (default: stdout)",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-V",
            help="Show detailed scoring information",
        ),
    ] = False,
) -> None:
    """Generate a context package from the specified directory.
    
    Scans the project, ranks files by relevance, and outputs Markdown.
    """
    directory = path.resolve()
    
    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise typer.Exit(1)
    
    # Load and merge config
    config = Config.load(directory)
    config = config.merge_cli_args(
        max_files=max_files,
        max_bytes=max_bytes,
        extensions=extensions,
        include_tests=include_tests,
        exclude_tests=exclude_tests,
        mode=mode,
    )
    
    # Load ignore patterns
    ignore_matcher = IgnoreMatcher.from_directory(directory)
    
    # Scan files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Scanning files...", total=None)
        files = list(scan_directory(directory, config, ignore_matcher))
    
    if not files:
        console.print("[yellow]No matching files found.[/yellow]")
        raise typer.Exit(0)
    
    # Filter files
    filtered = filter_files(files, config)
    
    if not filtered:
        console.print("[yellow]No files remaining after filtering.[/yellow]")
        raise typer.Exit(0)
    
    # Rank files
    if config.mode == "smart":
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Building import graph...", total=None)
            graph = build_import_graph(filtered, directory)
        
        scored = rank_files_smart(filtered, config, graph)
    else:
        scored = rank_files_simple(filtered, config)
    
    # Select top files
    selected = select_top_files(scored, config.max_files, config.max_bytes)
    
    if not selected:
        console.print("[yellow]No files selected within size limits.[/yellow]")
        raise typer.Exit(0)
    
    # Generate output
    markdown = generate_markdown(
        directory,
        selected,
        len(files),
        config,
        verbose=verbose,
    )
    
    # Write output
    if out:
        write_output(markdown, out)
        console.print(
            f"[green]✓[/green] Context package written to [cyan]{out}[/cyan] "
            f"({len(selected)} files)"
        )
    else:
        write_output(markdown, None)


@app.command()
def watch(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to watch (default: current directory)",
        ),
    ] = Path("."),
    out: Annotated[
        Path,
        typer.Option(
            "--out", "-o",
            help="Output file (required for watch mode)",
        ),
    ] = Path("ctxpack-output.md"),
    debounce: Annotated[
        Optional[float],
        typer.Option(
            "--debounce", "-d",
            help="Debounce delay in seconds",
        ),
    ] = None,
    max_files: Annotated[
        Optional[int],
        typer.Option(
            "--max-files", "-n",
            help="Maximum number of files",
        ),
    ] = None,
    max_bytes: Annotated[
        Optional[int],
        typer.Option(
            "--max-bytes", "-b",
            help="Maximum total size",
        ),
    ] = None,
    extensions: Annotated[
        Optional[str],
        typer.Option(
            "--extensions", "-e",
            help="Comma-separated extensions",
        ),
    ] = None,
    mode: Annotated[
        Optional[str],
        typer.Option(
            "--mode", "-m",
            help="Selection mode",
        ),
    ] = None,
    include_tests: Annotated[
        bool,
        typer.Option("--include-tests"),
    ] = False,
    exclude_tests: Annotated[
        bool,
        typer.Option("--exclude-tests"),
    ] = False,
) -> None:
    """Watch for file changes and auto-regenerate context package.
    
    Monitors the directory for changes and repacks automatically.
    """
    directory = path.resolve()
    
    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise typer.Exit(1)
    
    # Load and merge config
    config = Config.load(directory)
    config = config.merge_cli_args(
        max_files=max_files,
        max_bytes=max_bytes,
        extensions=extensions,
        include_tests=include_tests,
        exclude_tests=exclude_tests,
        mode=mode,
        debounce=debounce,
    )
    
    # Load ignore patterns
    ignore_matcher = IgnoreMatcher.from_directory(directory)
    
    repack_count = 0
    
    def do_pack() -> None:
        """Run pack and write output."""
        nonlocal repack_count
        repack_count += 1
        
        files = list(scan_directory(directory, config, ignore_matcher))
        if not files:
            return
        
        filtered = filter_files(files, config)
        if not filtered:
            return
        
        if config.mode == "smart":
            graph = build_import_graph(filtered, directory)
            scored = rank_files_smart(filtered, config, graph)
        else:
            scored = rank_files_simple(filtered, config)
        
        selected = select_top_files(scored, config.max_files, config.max_bytes)
        if not selected:
            return
        
        markdown = generate_markdown(directory, selected, len(files), config)
        write_output(markdown, out)
        
        console.print(
            f"[dim][{repack_count}][/dim] "
            f"[green]✓[/green] Repacked {len(selected)} files to [cyan]{out}[/cyan]"
        )
    
    def on_change(changed: list[str]) -> None:
        """Handle file changes."""
        # Show what changed
        for path in changed[:3]:
            console.print(f"  [dim]Changed:[/dim] {Path(path).name}")
        if len(changed) > 3:
            console.print(f"  [dim]...and {len(changed) - 3} more[/dim]")
        
        do_pack()
    
    # Initial pack
    console.print(Panel(
        f"Watching [cyan]{directory}[/cyan]\n"
        f"Output: [cyan]{out}[/cyan]\n"
        f"Mode: [cyan]{config.mode}[/cyan]\n\n"
        f"Press [bold]Ctrl+C[/bold] to stop",
        title="ctxpack watch",
        border_style="blue",
    ))
    
    do_pack()
    
    # Start watching
    watcher = FileWatcher(directory, config, ignore_matcher, on_change)
    
    try:
        watcher.start()
        watcher.wait()
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        console.print("\n[dim]Stopped watching.[/dim]")


if __name__ == "__main__":
    app()
