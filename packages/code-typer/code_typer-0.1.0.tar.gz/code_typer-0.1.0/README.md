# code-typer

Terminal-based code showcase tool that simulates human-like typing of source code files.

## Features

- **Human-like typing simulation** - Variable speed, occasional typos with corrections, natural pauses
- **Syntax highlighting** - Built-in support for Python and SQL, extensible for other languages
- **Multi-file support** - Showcase entire directories with smooth transitions
- **ncurses display** - Proper terminal handling with scrolling and color support
- **Configurable behavior** - Adjust typing speed and error rate

## Installation

```bash
pip install code-typer
```

For development with Cython optimizations:

```bash
pip install code-typer[dev]
```

## Usage

```bash
# Showcase a single file
showcase example.py

# Showcase with custom speed (2x faster)
showcase example.py --speed 2.0

# Showcase with higher error rate
showcase example.py --error-rate 0.05

# Showcase an entire directory
showcase ./src --speed 1.5

# Disable syntax highlighting
showcase example.py --no-highlight
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--speed, -s` | Typing speed multiplier (1.0 = normal) | 1.0 |
| `--error-rate, -e` | Probability of typos (0.0-1.0) | 0.02 |
| `--no-highlight` | Disable syntax highlighting | False |
| `--pause-between-files` | Pause duration between files (seconds) | 1.0 |

## Supported Languages

- Python (`.py`, `.pyx`, `.pxd`)
- SQL (`.sql`)

Additional languages will show without syntax highlighting.

## License

Apache License 2.0
