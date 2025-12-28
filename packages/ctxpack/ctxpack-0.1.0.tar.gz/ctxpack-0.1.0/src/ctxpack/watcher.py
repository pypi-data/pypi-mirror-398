"""File watching with debouncing for ctxpack watch mode."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ctxpack.config import Config
from ctxpack.ignore import IgnoreMatcher


class DebouncedHandler(FileSystemEventHandler):
    """File system event handler with debouncing."""
    
    def __init__(
        self,
        root: Path,
        config: Config,
        ignore_matcher: IgnoreMatcher,
        callback: Callable[[list[str]], None],
    ) -> None:
        """Initialize the handler.
        
        Args:
            root: Root directory being watched
            config: Configuration with debounce settings
            ignore_matcher: Pattern matcher for ignoring files
            callback: Function to call after debounce with list of changed paths
        """
        super().__init__()
        self.root = root
        self.config = config
        self.ignore_matcher = ignore_matcher
        self.callback = callback
        
        self._pending_changes: set[str] = set()
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
    
    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored."""
        p = Path(path)
        
        # Ignore directories
        if p.is_dir():
            return True
        
        # Check ignore patterns
        if self.ignore_matcher.is_ignored(p, self.root):
            return True
        
        # Check extension
        ext = p.suffix.lower()
        if ext not in self.config.extensions:
            return True
        
        return False
    
    def _schedule_callback(self) -> None:
        """Schedule callback after debounce delay."""
        with self._lock:
            # Cancel existing timer
            if self._timer is not None:
                self._timer.cancel()
            
            # Schedule new timer
            self._timer = threading.Timer(
                self.config.debounce_seconds,
                self._fire_callback,
            )
            self._timer.start()
    
    def _fire_callback(self) -> None:
        """Fire the callback with pending changes."""
        with self._lock:
            changes = list(self._pending_changes)
            self._pending_changes.clear()
            self._timer = None
        
        if changes:
            self.callback(changes)
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if self._should_ignore(event.src_path):
            return
        
        with self._lock:
            self._pending_changes.add(event.src_path)
        
        self._schedule_callback()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if self._should_ignore(event.src_path):
            return
        
        with self._lock:
            self._pending_changes.add(event.src_path)
        
        self._schedule_callback()
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        # Still trigger repack on deletion
        if event.is_directory:
            return
        
        with self._lock:
            self._pending_changes.add(event.src_path)
        
        self._schedule_callback()
    
    def stop(self) -> None:
        """Stop any pending timers."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


class FileWatcher:
    """Watches directory for changes and triggers repacking."""
    
    def __init__(
        self,
        root: Path,
        config: Config,
        ignore_matcher: IgnoreMatcher,
        on_change: Callable[[list[str]], None],
    ) -> None:
        """Initialize the watcher.
        
        Args:
            root: Directory to watch
            config: Configuration
            ignore_matcher: Ignore pattern matcher
            on_change: Callback for changes (receives list of changed paths)
        """
        self.root = root.resolve()
        self.config = config
        self.ignore_matcher = ignore_matcher
        self.on_change = on_change
        
        self._observer: Observer | None = None
        self._handler: DebouncedHandler | None = None
    
    def start(self) -> None:
        """Start watching for file changes."""
        self._handler = DebouncedHandler(
            self.root,
            self.config,
            self.ignore_matcher,
            self.on_change,
        )
        
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(self.root),
            recursive=True,
        )
        self._observer.start()
    
    def stop(self) -> None:
        """Stop watching."""
        if self._handler is not None:
            self._handler.stop()
        
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2.0)
    
    def wait(self) -> None:
        """Block until interrupted."""
        if self._observer is not None:
            try:
                while self._observer.is_alive():
                    self._observer.join(timeout=1.0)
            except KeyboardInterrupt:
                pass
