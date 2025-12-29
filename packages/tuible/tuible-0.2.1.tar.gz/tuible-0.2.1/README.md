# Tuible

A Python package for printing formatted CLI tables with ANSI colors.

## Features

- Print single table lines or multi-row table blocks
- ANSI color support for borders and data
- Customizable column widths and alignment
- head formatting with underline styles
- Auto-sizing based on content
- Multi-row cells using colon prefix syntax
- Index column support for numbered rows

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
tuible top head "Name" "Age" body "John" "25" bot

# With custom colors and formatting
tuible body -ce 31 -cb 32 "Red Border" "Green body"

# With index column (numbered rows)
tuible top head "Name" "Age" index body "Alice" "25" body "Bob" "30" bot

# With index and custom colors
tuible -ch 33 -ci 35 -fic index top head "Item" "Quantity" body "Apples" "5" body "Oranges" "3" bot

# The order doesn't matter.
tuible body b1 head h1
```

#### Modes
- `body`: Print body line
- `head`: Print head line
- `index` / `idx`: Add an index column before the rest of the table (must come before head/body)
- `top`: Print top border
- `bot`: Print bottom border

#### Options
- `-ce <color>`: Set edge color (e.g., 34 for blue)
- `-cb <color>`: Set body color (e.g., 32 for green)
- `-ch <color>`: Set head color (e.g., 33 for yellow)
- `-ci <color>`: Set index color (e.g., 35 for magenta)
- `-fb <style>`: Set body style (e.g., 4 for underline)
- `-fh <style>`: Set head style
- `-fi <style>`: Set index style (e.g., 4 for underline, 1 for bold)
- `-fe <chars>`: Set edge characters (8 chars: left-right, top-bottom, corners, middle)
- `-size <num>`: Set column width (-1 for dynamic)
- `-nb`: No border (left and right)
- `-nhi`: Hide the auto-generated header index while auto-numbering
- `-fic`: Center-align index column
- `-fil`: Left-align index column
- `-fir`: Right-align index column

### Index Column

The `index` command reserves the leftmost column for explicit labels or auto-numbering. It must appear before `head` or `body` in the invocation. Provide plain labels (e.g., `i1`) for header rows and colon-prefixed labels (e.g., `:i1`) for body rows. Omitting all labels triggers auto-numbering (header rows start at `0`, body rows begin at `1`). Use empty strings (`''`) when you need a blank placeholder, and let the column width grow to the widest provided label (auto-numbering keeps a fixed 3-character width).

By default the index column renders in red italic text, but you can override the color and style with `-ci`/`-fi`.

### Examples

**Example 1 - Header + body labels:**
```bash
tuible index 'ih' ':i1' ':i2' head 'h1' 'h2' body 'b1' ':b11' 'b2' ':b21'
```
```
┃ih┃h1 ┃h2 ┃
┃i1┃b1 ┃b2 ┃
┃i2┃b11┃b21┃
```

**Example 2 - Body-only labels:**
```bash
tuible idx ':i1' ':i2' body b1 :b11 '' :b21
```
```
┃i1┃b1 ┃   ┃
┃i2┃b11┃b21┃
```

**Example 3 - Auto-numbering:**
```bash
tuible index head 'col1' 'col2' body 'b1' ':b11' '' ':b21'
```
```
┃  0┃col1┃col2┃
┃  1┃b1  ┃    ┃
┃  2┃b11 ┃b21 ┃
```

## Multi-row Cells (Colon Mechanics)
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
