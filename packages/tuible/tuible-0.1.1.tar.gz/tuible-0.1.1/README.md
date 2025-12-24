# Tuible

A Python package for printing formatted CLI tables with ANSI colors.

## Features

- Print single table lines or multi-row table blocks
- ANSI color support for borders and data
- Customizable column widths and alignment
- head formatting with underline styles
- Auto-sizing based on content
- Multi-row cells using colon prefix syntax

## Installation

```bash
pip install tuible
```

Or using uv:

```bash
uv pip install tuible
```

## Usage

### Python API

```python
from tuible import print_line, print_block, print_table

# Print a single line
print_line(['Name', 'Age', 'City'], colsize=15, color1='36', color2='35')

# Print a table block
rows = [
    ['Name', 'Age', 'City'],
    ['John', '25', 'New York'],
    ['Jane', '30', 'London']
]
print_block(rows, colsize=-1)  # Auto-size columns

# Print a full table with borders
print_table(heads=['Name', 'Age'], body=[['John', '25'], ['Jane', '30']])
```

### Command Line

The CLI uses a mode-based approach where you can stack different parts of the table.

```bash
# Print a single body line
tuible body "Name" "Age" "City"

# Print a header and body
tuible head "Name" "Age" body "John" "25"

# Print a full table with borders
tuible top head "Name" "Age" body "John" "25" bot -cc 2

# With custom colors and formatting
tuible body -ce 31 -cb 32 "Red Border" "Green body"

# The order doesn't matter.
tuible body b1 head h1
```

#### Modes
- `body`: Print body line
- `head`: Print head line
- `top`: Print top border
- `bot`: Print bottom border

#### Options
- `-ce <color>`: Set edge color (e.g., 34 for blue)
- `-cb <color>`: Set body color (e.g., 32 for green)
- `-ch <color>`: Set head color (e.g., 33 for yellow)
- `-fb <style>`: Set body style (e.g., 4 for underline)
- `-fh <style>`: Set head style
- `-fe <chars>`: Set edge characters (8 chars: left-right, top-bottom, corners, middle)
- `-size <num>`: Set column width (-1 for dynamic)
- `-cc <num>`: Set column count
- `-nb`: No border (left and right)

### Multi-row Cells (Colon Mechanics)
Elements starting with `:` are treated as continuations in the same column, allowing multi-row content within a single table column.

```bash
tuible body "Row 1" ":Row 2" "Other Col"
```

## API Reference

### `print_line(columns, colsize=25, color1='36', color2='35', format_style='', is_centered=False)`
Print a single line of table columns.

### `print_block(rows, colsize=-1, color1='36', color2='35', format_style='', format_head='4;', is_centered=False)`
Print a block of table rows.

### `print_table(heads=None, body=None, colsize=-1)`
Print a complete table with optional heads, body, and borders.

## Development

### Setup

```bash
git clone https://github.com/frank/tuible.git
cd tuible
uv sync
```

### Testing

```bash
PYTHONPATH=src uv run pytest
```

## License

MIT License - see LICENSE file for details.
