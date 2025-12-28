# ctxpack

**Automatically gather project context and generate Markdown prompt packages for LLMs.**

Stop manually copy-pasting files into ChatGPT. `ctxpack` intelligently selects the most relevant files from your project and packages them into a single Markdown document ready for any LLM.

## Installation

```bash
pip install ctxpack
```

## Quick Start

```bash
# Initialize ctxpack in your project
cd my-project
ctxpack init

# Generate a context package
ctxpack pack

# Generate with smart mode (import/reference analysis)
ctxpack pack --mode smart

# Watch for changes and auto-regenerate
ctxpack watch --out context.md
```

## Commands

### `ctxpack init`

Creates a `.ctxpack/` configuration folder and `.ctxpackignore` file with sensible defaults.

```bash
ctxpack init          # Initialize in current directory
ctxpack init --force  # Overwrite existing configuration
```

### `ctxpack pack [PATH]`

Scans your project, ranks files by relevance, and outputs a Markdown context package.

```bash
ctxpack pack                           # Pack current directory
ctxpack pack ./src                     # Pack specific path
ctxpack pack --max-files 10            # Limit to 10 files
ctxpack pack --max-bytes 50000         # Limit to 50KB
ctxpack pack --extensions .py,.js      # Only Python and JavaScript
ctxpack pack --include-tests           # Include test files
ctxpack pack --mode smart              # Use import graph analysis
ctxpack pack --out context.md          # Output to file
ctxpack pack --verbose                 # Show scoring details
```

### `ctxpack watch [PATH]`

Watches for file changes and auto-regenerates the context package.

```bash
ctxpack watch --out context.md         # Watch and output to file
ctxpack watch --debounce 2.0           # Wait 2 seconds after changes
```

## Configuration

After running `ctxpack init`, you can customize `.ctxpack/config.toml`:

```toml
[pack]
max_files = 20
max_bytes = 100000
extensions = [".py", ".ts", ".js", ".md"]
exclude_tests = true
mode = "simple"

[scoring]
recency_weight = 0.7
size_weight = 0.3
```

## Selection Modes

- **Simple mode** (default): Ranks files by recency and size
- **Smart mode**: Adds import/reference graph analysis to boost frequently-used files

## License

MIT
