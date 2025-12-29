"""Tuible table rendering logic."""

from typing import List, Set
from .params import TuibleParams


class TuibleTable:
    """Tuible Table Generator

    This class handles the rendering and execution of formatted Tuible tables based on TuibleParams.
    It provides methods for generating table borders, heads, and body rows with customizable
    formatting, colors, and alignments.

    Key Features:
    - Border rendering (top/bottom edges with customizable symbols)
    - head and body row rendering with alignment support
    - Dynamic column width calculation based on content
    - ANSI color and style support for visual formatting
    - Support for no-border mode for compact output
    - Multi-row cells within columns using colon prefix syntax

    Colon Mechanics:
    ----------------
    Elements starting with ':' are treated as continuations in the same column,
    allowing multi-row content within a single table column. This enables complex
    table layouts where cells can span multiple rows.

    Usage Pattern:
        # Parse command-line arguments
        params = TuibleParams.createFromArguments()
        if params:
            # Create table renderer
            table = TuibleTable(params)
            # Execute rendering based on mode stack
            table.execute()

    The class processes a mode stack that can include 'top', 'head', 'body', and 'bot'
    modes in any combination, allowing flexible table composition.
    """

    def __init__(self, params: TuibleParams):
        """Initialize TuibleTable with parameters."""
        self.params = params
        self.format_index = params.format_index
        if self.params.size == -1 or 'idx' in self.params.mode_columns:
            self.calculate_dynamic_widths()

    def calculate_dynamic_widths(self) -> None:
        """Calculate dynamic column widths based on the widest element in each column."""
        if not self.params.column_count:
            return

        # Initialize widths for each column
        self.params.column_widths = [0] * self.params.column_count

        # Handle index column first if present
        if 'idx' in self.params.mode_columns:
            if self.params.index_auto_numbering:
                idx_width = max(3, self.params.format_index.get('size', 3))
            else:
                index_entries = self.params.index_header_values + self.params.index_body_values
                max_width = max((len(cell) for cell in index_entries), default=0)
                idx_width = max(1, max_width)
            self.params.column_widths[0] = idx_width

        # Iterate through other modes and find the max width for each column
        for mode, columns in self.params.mode_columns.items():
            if mode == 'idx':
                continue  # Already handled above

            # Offset for other columns if index is present
            offset = 1 if 'idx' in self.params.mode_columns else 0
            for col_idx, column in enumerate(columns):
                max_width = max((len(cell) for cell in column), default=0)
                if self.params.size != -1:
                    max_width = max(max_width, self.params.size)
                if col_idx + offset < len(self.params.column_widths):
                    self.params.column_widths[col_idx + offset] = max(self.params.column_widths[col_idx + offset], max_width)

        # Ensure minimum width of 1 for empty columns
        self.params.column_widths = [max(1, w) for w in self.params.column_widths]
    
    def _align_text(self, text: str, width: int, alignment: str) -> str:
        """Align text within a given width."""
        text_len = len(text)
        if text_len >= width:
            return text[:width]
        
        if alignment == 'center':
            left_pad = (width - text_len) // 2
            right_pad = width - text_len - left_pad
            return ' ' * left_pad + text + ' ' * right_pad
        elif alignment == 'right':
            return ' ' * (width - text_len) + text
        else:  # left
            return text + ' ' * (width - text_len)
    
    def render_top(self) -> None:
        """Render the top border of the table."""
        if self.params.no_border:
            return

        edge_color = f"\x1b[{self.params.format_edge['color']}m"
        reset = "\x1b[0m"

        # Get column count
        col_count = self.params.column_count if self.params.column_count else len(self.params.columns)

        # Build top border
        line = edge_color + self.params.format_edge['symbol_topleft']
        for i in range(col_count):
            width = self.params.column_widths[i] if self.params.column_widths else self.params.size
            line += self.params.format_edge['symbol_topbottom'] * width
            if i < col_count - 1:
                line += self.params.format_edge['symbol_topmiddle']
        line += self.params.format_edge['symbol_topright'] + reset
        print(line)
    
    def render_bottom(self) -> None:
        """Render the bottom border of the table."""
        if self.params.no_border:
            return

        edge_color = f"\x1b[{self.params.format_edge['color']}m"
        reset = "\x1b[0m"

        # Get column count
        col_count = self.params.column_count if self.params.column_count else len(self.params.columns)

        # Build bottom border
        line = edge_color + self.params.format_edge['symbol_bottomleft']
        for i in range(col_count):
            width = self.params.column_widths[i] if self.params.column_widths else self.params.size
            line += self.params.format_edge['symbol_topbottom'] * width
            if i < col_count - 1:
                line += self.params.format_edge['symbol_bottommiddle']
        line += self.params.format_edge['symbol_bottomright'] + reset
        print(line)
    
    def render_head(self) -> None:
        """Render head rows from columns."""
        if 'head' not in self.params.mode_columns or not self.params.mode_columns['head']:
            return

        columns = self.params.mode_columns['head']
        max_rows = len(columns[0]) if columns else 0
        idx_enabled = 'idx' in self.params.mode_columns
        offset = 1 if idx_enabled else 0

        for row_idx in range(max_rows):
            index_cell = self._get_index_value(row_idx, is_head=True)
            self._render_row(row_idx, columns, is_head=True, index_cell=index_cell, offset=offset)

    def render_body(self) -> None:
        """Render body rows from columns."""
        if 'body' not in self.params.mode_columns or not self.params.mode_columns['body']:
            return

        columns = self.params.mode_columns['body']
        max_rows = len(columns[0]) if columns else 0

        # Determine how many index cells were already used by the header
        head_rows = len(self.params.mode_columns['head'][0]) if 'head' in self.params.mode_columns and self.params.mode_columns['head'] else 0
        idx_enabled = 'idx' in self.params.mode_columns
        offset = 1 if idx_enabled else 0

        for row_idx in range(max_rows):
            index_cell = self._get_index_value(row_idx, is_head=False, head_rows=head_rows)
            self._render_row(row_idx, columns, is_head=False, index_cell=index_cell, offset=offset)
    
    def _render_row(self, row_idx: int, columns: List[List[str]], is_head: bool = False, index_cell: str = "", offset: int = 0) -> None:
        """Render a single row of body."""
        format_dict = self.params.format_head if is_head else self.params.format_body

        edge_color = f"\x1b[{self.params.format_edge['color']}m"
        body_color = f"\x1b[{format_dict['esc']}{format_dict['color']}m"
        index_color = f"\x1b[{self.format_index['esc']}{self.format_index['color']}m"
        reset = "\x1b[0m"

        # Start with left border
        if not self.params.no_border:
            print(edge_color + self.params.format_edge['symbol_leftright'], end='')

        # Print index cell if index is present
        if 'idx' in self.params.mode_columns:
            if self.params.column_widths:
                width = self.params.column_widths[0]
            elif self.params.index_auto_numbering:
                width = max(3, self.format_index.get('size', 3))
            else:
                width = self.params.size
            text = index_cell[:width]  # truncate to width
            aligned_text = self._align_text(text, width, self.format_index['align'])
            print(index_color + aligned_text + reset, end='')
            if not self.params.no_border:
                print(edge_color + self.params.format_edge['symbol_leftright'], end='')

        # Print each column's cell for this row
        for col_idx, column in enumerate(columns):
            cell_text = column[row_idx] if row_idx < len(column) else ""
            # Use dynamic width if available, otherwise use fixed size
            width = self.params.column_widths[col_idx + offset] if self.params.column_widths else self.params.size
            text = cell_text[:width]  # truncate to width
            aligned_text = self._align_text(text, width, format_dict['align'])

            print(body_color + aligned_text + reset, end='')

            # Print column separator if not the last column
            if not self.params.no_border and col_idx < len(columns) - 1:
                print(edge_color + self.params.format_edge['symbol_leftright'], end='')
            elif not self.params.no_border:
                # Print right border for last column (only if not no_border)
                print(edge_color + self.params.format_edge['symbol_leftright'], end='')

        print()  # newline after row

    def _get_index_value(self, row_idx: int, is_head: bool = False, head_rows: int = 0) -> str:
        if 'idx' not in self.params.mode_columns:
            return ""
        if self.params.index_auto_numbering:
            if is_head:
                if self.params.no_header_index:
                    return ""
                return str(row_idx)
            start = head_rows if head_rows > 0 else 1
            return str(start + row_idx)
        if is_head:
            return self.params.index_header_values[row_idx] if row_idx < len(self.params.index_header_values) else ""
        if row_idx < len(self.params.index_body_values):
            return self.params.index_body_values[row_idx]
        extra_index = head_rows + row_idx
        if extra_index < len(self.params.index_header_values):
            return self.params.index_header_values[extra_index]
        return ""

    def execute(self) -> None:
        """Execute all modes in the mode stack, calling each render method only once."""
        executed_modes: Set[str] = set()
        for mode in self.params.mode_stack:
            if mode not in executed_modes:
                executed_modes.add(mode)
                if mode == 'top':
                    self.render_top()
                elif mode == 'bot':
                    self.render_bottom()
                elif mode == 'head':
                    self.render_head()
                elif mode == 'body':
                    self.render_body()
