"""Core functions for printing CLI tables."""

from typing import List, Union, Any, Optional
from .params import TuibleParams
from .table import TuibleTable


def print_line(
    columns: List[Any],
    colsize: Union[int, List[int]] = 25,
    color1: str = '36',
    color2: str = '35',
    format_style: str = '',
    is_centered: bool = False
) -> None:
    """
    Print a single line of table columns with formatting.

    Args:
        columns: List of column values to print.
        colsize: Column size(s). If int, applies to all columns. If list, per column.
        color1: ANSI color code for borders (default: '36' cyan).
        color2: ANSI color code for body (default: '35' magenta).
        format_style: Additional style for body (e.g., '4;' for underline).
        is_centered: Whether to center-align the body.
    """
    params = TuibleParams()
    params.format_edge['color'] = color1
    params.format_body['color'] = color2
    params.format_body['esc'] = format_style
    params.format_body['align'] = 'center' if is_centered else 'left'
    
    if isinstance(colsize, int):
        params.size = colsize
        params.column_count = len(columns)
    else:
        params.column_widths = colsize
        params.column_count = len(columns)

    # Prepare body mode
    params.mode_stack = ['body']
    params.mode_columns['body'] = [[str(col)] for col in columns]
    
    table = TuibleTable(params)
    table.execute()


def print_block(
    rows: List[List[Any]],
    colsize: int = -1,
    color1: str = '36',
    color2: str = '35',
    format_style: str = '',
    format_head: str = '4;',
    is_centered: bool = False
) -> None:
    """
    Print a block of table rows with formatting.

    Args:
        rows: List of rows, each row is a list of columns.
        colsize: Column size. -1 for auto-size based on longest entry.
        color1: ANSI color code for borders (default: '36' cyan).
        color2: ANSI color code for body (default: '35' magenta).
        format_style: Additional style for body rows.
        format_head: Style for head row (default: '4;' underline).
        is_centered: Whether to center-align the body.
    """
    if not rows:
        return

    params = TuibleParams()
    params.format_edge['color'] = color1
    params.format_body['color'] = color2
    params.format_body['esc'] = format_style
    params.format_body['align'] = 'center' if is_centered else 'left'
    params.format_head['esc'] = format_head
    params.size = colsize
    
    # In TuibleParams, body is stored as columns: List[List[str]]
    # We need to transpose rows to columns
    num_cols = len(rows[0])
    head_row = rows[0]
    body_rows = rows[1:]
    
    params.mode_stack = ['head', 'body']
    
    # head columns
    params.mode_columns['head'] = [[str(cell)] for cell in head_row]
    
    # body columns
    body_cols = [[] for _ in range(num_cols)]
    for row in body_rows:
        for i in range(num_cols):
            val = str(row[i]) if i < len(row) else ""
            body_cols[i].append(val)
    params.mode_columns['body'] = body_cols
    
    # Set column count for proper width calculation
    params.column_count = num_cols


    table = TuibleTable(params)
    table.execute()


def print_table(
    heads: Optional[List[str]] = None,
    body: Optional[List[List[str]]] = None,
    colsize: int = -1
) -> None:
    """
    Print a complete table with optional heads, body, and borders.

    Args:
        heads: List of head strings
        body: List of body rows
        colsize: Column size (-1 for auto)
    """
    rows = []
    if heads:
        rows.append(heads)
    if body:
        rows.extend(body)
    
    if not rows:
        return

    params = TuibleParams()
    params.size = colsize
    params.mode_stack = ['top', 'head', 'body', 'bot']
    
    num_cols = len(rows[0])
    params.column_count = num_cols
    
    if heads:
        params.mode_columns['head'] = [[str(cell)] for cell in heads]
    
    if body:
        body_cols = [[] for _ in range(num_cols)]
        for row in body:
            for i in range(num_cols):
                val = str(row[i]) if i < len(row) else ""
                body_cols[i].append(val)
        params.mode_columns['body'] = body_cols


    table = TuibleTable(params)
    table.execute()
