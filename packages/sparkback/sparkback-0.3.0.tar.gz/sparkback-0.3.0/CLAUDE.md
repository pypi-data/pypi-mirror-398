# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sparkback is a Python library for generating sparklines in the terminal using various Unicode characters. It provides both a command-line tool and a Python API for visualizing numerical data as compact inline graphs.

## Development Setup

```bash
uv sync --all-extras
```

## Common Commands

### Running the CLI
```bash
# Using uv run
uv run spark --ticks default 10 20 30 40 50

# Or directly via bin/spark
bin/spark --ticks default 10 20 30 40 50
```

### Testing
```bash
# Run all tests
uv run pytest

# Run a specific test
uv run pytest tests/spark_test.py::test_scale_data_default
```

### Linting and Formatting
```bash
# Format code with Black
uv run black sparkback/ tests/

# Run linters (all configured for 120 character line length)
uv run flake8 sparkback/ tests/
uv run pylint sparkback/
```

### Building
```bash
uv build
```

## Architecture

The codebase is structured around a simple object-oriented design pattern:

### Core Components

1. **AbstractStyle Base Class** (sparkback/spark.py:53-72)
   - Defines the interface for all visualization styles
   - Single abstract method: `scale_data(data, verbose=False)`

2. **Style Implementations**
   All style classes inherit from AbstractStyle and implement the `scale_data` method:
   - **DefaultStyle**: Unicode blocks (▁▂▃▄▅▆▇█) - scales linearly to data range
   - **BlockStyle**: Alternative blocks (▏▎▍▌▋▊▉█) - inherits DefaultStyle's scaling
   - **AsciiStyle**: ASCII characters (.oO#@) - inherits DefaultStyle's scaling
   - **NumericStyle**: Numbers (1-5) - inherits DefaultStyle's scaling
   - **BrailleStyle**: Braille characters (⣀⣤⣶⣿) - inherits DefaultStyle's scaling
   - **ArrowsStyle**: Directional indicators (↓→↗↑) - shows trend between consecutive values
   - **MultiLineGraphStyle**: Vertical bar chart rendered across 10 lines
   - **LineGraphStyle**: Connected line graphs using box-drawing characters (─│╱╲●) - configurable height

3. **Key Functions**
   - `get_style_instance(style)`: Factory function returning style instances from the STYLES dict
   - `print_ansi_spark(data_points, verbose, style)`: Renders sparklines (handles both single-line and multi-line output)
   - `print_stats(data)`: Computes min, max, mean, and standard deviation

### Data Flow

1. CLI arguments parsed via `get_args()` → returns argparse.Namespace
2. Style instance created via `get_style_instance(args.ticks)` → returns AbstractStyle subclass
3. Data scaled via `style_instance.scale_data(args.numbers)` → returns list of characters or 2D grid
4. Output via `print_ansi_spark(scaled_data)` → prints to terminal

### Adding a New Style

To add a new visualization style:
1. Create a class inheriting from AbstractStyle
2. Define the `scale_data(data, verbose)` method
3. Add the class to the STYLES dictionary in sparkback/spark.py:185-193
4. The new style will automatically appear in CLI `--ticks` choices

## Code Standards

- Line length: 120 characters (enforced by Black, flake8, pylint)
- Python version: >=3.8.1
- Test files use: `# flake8: noqa` and `# pylint: skip-file`
