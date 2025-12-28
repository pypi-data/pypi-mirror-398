"""Configuration management for ctxpack."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Default extensions to include
DEFAULT_EXTENSIONS = [
    ".py", ".pyi",
    ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".scala",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c", ".cpp", ".cc", ".h", ".hpp",
    ".cs",
    ".swift",
    ".md", ".mdx",
    ".json", ".yaml", ".yml", ".toml",
    ".sql",
    ".sh", ".bash",
    ".html", ".css", ".scss",
    ".vue", ".svelte",
]

# Default ignore patterns for .ctxpackignore
DEFAULT_IGNORE_PATTERNS = """\
# Version control
.git/
.svn/
.hg/

# Dependencies
node_modules/
vendor/
.venv/
venv/
env/
__pycache__/
*.pyc
.eggs/
*.egg-info/

# Build outputs
dist/
build/
target/
out/
.next/
.nuxt/
.output/
coverage/

# IDE/Editor
.idea/
.vscode/
*.swp
*.swo
*~
.project
.classpath
.settings/

# OS files
.DS_Store
Thumbs.db
Desktop.ini

# Package lock files
package-lock.json
yarn.lock
pnpm-lock.yaml
Cargo.lock
poetry.lock
Pipfile.lock
composer.lock
Gemfile.lock

# Binary/Media
*.png
*.jpg
*.jpeg
*.gif
*.ico
*.svg
*.webp
*.woff
*.woff2
*.ttf
*.eot
*.otf
*.mp3
*.mp4
*.wav
*.ogg
*.webm
*.avi
*.mov
*.zip
*.tar
*.gz
*.rar
*.7z
*.pdf
*.doc
*.docx
*.xls
*.xlsx
*.ppt
*.pptx

# Logs and databases
*.log
*.sqlite
*.sqlite3
*.db

# Environment
.env
.env.*
!.env.example

# ctxpack
.ctxpack/
"""


@dataclass
class Config:
    """Configuration for ctxpack operations."""
    
    # Pack settings
    max_files: int = 20
    max_bytes: int = 100_000  # 100KB
    extensions: list[str] = field(default_factory=lambda: DEFAULT_EXTENSIONS.copy())
    exclude_tests: bool = True
    mode: str = "simple"  # "simple" or "smart"
    
    # Scoring weights (for simple mode)
    recency_weight: float = 0.7
    size_weight: float = 0.3
    
    # Smart mode settings
    import_boost: float = 0.1
    reference_boost: float = 0.05
    
    # Watch settings
    debounce_seconds: float = 1.0
    
    @classmethod
    def load(cls, directory: Path) -> Config:
        """Load configuration from .ctxpack/config.toml.
        
        Args:
            directory: Project root directory
            
        Returns:
            Config instance (default if no config file)
        """
        config_path = directory / ".ctxpack" / "config.toml"
        
        if not config_path.exists():
            return cls()
        
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            return cls.from_dict(data)
        except Exception:
            return cls()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create Config from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Config instance
        """
        config = cls()
        
        pack = data.get("pack", {})
        if "max_files" in pack:
            config.max_files = int(pack["max_files"])
        if "max_bytes" in pack:
            config.max_bytes = int(pack["max_bytes"])
        if "extensions" in pack:
            config.extensions = list(pack["extensions"])
        if "exclude_tests" in pack:
            config.exclude_tests = bool(pack["exclude_tests"])
        if "mode" in pack:
            config.mode = str(pack["mode"])
        
        scoring = data.get("scoring", {})
        if "recency_weight" in scoring:
            config.recency_weight = float(scoring["recency_weight"])
        if "size_weight" in scoring:
            config.size_weight = float(scoring["size_weight"])
        if "import_boost" in scoring:
            config.import_boost = float(scoring["import_boost"])
        if "reference_boost" in scoring:
            config.reference_boost = float(scoring["reference_boost"])
        
        watch = data.get("watch", {})
        if "debounce_seconds" in watch:
            config.debounce_seconds = float(watch["debounce_seconds"])
        
        return config
    
    def to_toml(self) -> str:
        """Convert config to TOML string.
        
        Returns:
            TOML-formatted string
        """
        ext_list = ", ".join(f'"{e}"' for e in self.extensions)
        return f'''\
# ctxpack configuration
# See https://github.com/gabriel/ctxpack for documentation

[pack]
# Maximum number of files to include
max_files = {self.max_files}

# Maximum total output size in bytes
max_bytes = {self.max_bytes}

# File extensions to include
extensions = [{ext_list}]

# Exclude test files (files matching test patterns)
exclude_tests = {str(self.exclude_tests).lower()}

# Selection mode: "simple" (recency + size) or "smart" (adds import analysis)
mode = "{self.mode}"

[scoring]
# Weight for file recency (0.0 to 1.0)
recency_weight = {self.recency_weight}

# Weight for file size - smaller files score higher (0.0 to 1.0)
size_weight = {self.size_weight}

# Boost for files that import other files (smart mode)
import_boost = {self.import_boost}

# Boost for files that are referenced by others (smart mode)
reference_boost = {self.reference_boost}

[watch]
# Seconds to wait after last file change before repacking
debounce_seconds = {self.debounce_seconds}
'''

    def merge_cli_args(
        self,
        max_files: int | None = None,
        max_bytes: int | None = None,
        extensions: str | None = None,
        include_tests: bool = False,
        exclude_tests: bool = False,
        mode: str | None = None,
        debounce: float | None = None,
    ) -> Config:
        """Create new config with CLI arguments merged in.
        
        CLI arguments take precedence over config file values.
        
        Returns:
            New Config instance with merged values
        """
        # Create a copy
        config = Config(
            max_files=self.max_files,
            max_bytes=self.max_bytes,
            extensions=self.extensions.copy(),
            exclude_tests=self.exclude_tests,
            mode=self.mode,
            recency_weight=self.recency_weight,
            size_weight=self.size_weight,
            import_boost=self.import_boost,
            reference_boost=self.reference_boost,
            debounce_seconds=self.debounce_seconds,
        )
        
        if max_files is not None:
            config.max_files = max_files
        if max_bytes is not None:
            config.max_bytes = max_bytes
        if extensions is not None:
            config.extensions = [e.strip() for e in extensions.split(",")]
            # Ensure extensions start with dot
            config.extensions = [
                e if e.startswith(".") else f".{e}"
                for e in config.extensions
            ]
        if include_tests:
            config.exclude_tests = False
        elif exclude_tests:
            config.exclude_tests = True
        if mode is not None:
            config.mode = mode
        if debounce is not None:
            config.debounce_seconds = debounce
        
        return config


def create_default_ignore_file(path: Path) -> None:
    """Create default .ctxpackignore file.
    
    Args:
        path: Path where to create the file
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(DEFAULT_IGNORE_PATTERNS)


def init_ctxpack(directory: Path, force: bool = False) -> tuple[bool, str]:
    """Initialize ctxpack in a directory.
    
    Args:
        directory: Project root directory
        force: Overwrite existing files
        
    Returns:
        Tuple of (success, message)
    """
    ctxpack_dir = directory / ".ctxpack"
    config_file = ctxpack_dir / "config.toml"
    ignore_file = directory / ".ctxpackignore"
    
    # Check if already initialized
    if ctxpack_dir.exists() and not force:
        return False, f"Already initialized. Use --force to overwrite."
    
    # Create .ctxpack directory
    ctxpack_dir.mkdir(parents=True, exist_ok=True)
    
    # Write config file
    config = Config()
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config.to_toml())
    
    # Write ignore file
    create_default_ignore_file(ignore_file)
    
    return True, f"Initialized ctxpack in {directory}"
