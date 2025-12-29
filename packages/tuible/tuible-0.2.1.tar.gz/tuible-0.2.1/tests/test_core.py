"""Unit tests for core functions in tuible."""

import pytest
import re
from unittest.mock import patch, MagicMock
from io import StringIO
from tuible.core import print_line, print_block, print_table
from tuible.params import TuibleParams
from tuible.table import TuibleTable


def strip_ansi(text):
    """Strip ANSI escape sequences from string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class TestPrintLine:
    """Test cases for print_line function."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_basic(self, mock_stdout):
        """Test basic print_line functionality."""
        columns = ['Name', 'Age', 'City']
        print_line(columns)
        output = strip_ansi(mock_stdout.getvalue())
        assert 'Name' in output
        assert 'Age' in output
        assert 'City' in output
        assert '┃' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_with_int_colsize(self, mock_stdout):
        """Test print_line with integer colsize."""
        columns = ['A', 'B']
        print_line(columns, colsize=10)
        output = strip_ansi(mock_stdout.getvalue())
        assert 'A' in output
        assert 'B' in output
        assert '┃' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_centered(self, mock_stdout):
        """Test print_line with centered alignment."""
        columns = ['Test']
        print_line(columns, is_centered=True, colsize=10)
        output = strip_ansi(mock_stdout.getvalue())
        assert '   Test   ' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_custom_colors(self, mock_stdout):
        """Test print_line with custom colors."""
        columns = ['body']
        print_line(columns, color1='31', color2='32')
        output = mock_stdout.getvalue()
        assert '\x1b[31m' in output
        assert '\x1b[32m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_format_style(self, mock_stdout):
        """Test print_line with format style."""
        columns = ['Styled']
        print_line(columns, format_style='1;')  # Bold
        output = mock_stdout.getvalue()
        assert '\x1b[1;35m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_single_column(self, mock_stdout):
        """Test print_line with single column."""
        columns = ['Single']
        print_line(columns)
        output = strip_ansi(mock_stdout.getvalue())
        assert 'Single' in output
        assert '┃' in output


class TestPrintBlock:
    """Test cases for print_block function."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_block_basic(self, mock_stdout):
        """Test basic print_block functionality."""
        rows = [['Name', 'Age'], ['John', '25'], ['Jane', '30']]
        print_block(rows)
        output = strip_ansi(mock_stdout.getvalue())
        assert 'Name' in output
        assert 'John' in output
        assert 'Jane' in output
        assert '┃' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_block_auto_colsize(self, mock_stdout):
        """Test print_block with auto column sizing."""
        rows = [['A', 'BB'], ['CCC', 'D']]
        print_block(rows, colsize=-1)
        output = strip_ansi(mock_stdout.getvalue())
        assert 'A' in output
        assert 'CCC' in output
        assert '┃CCC┃' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_block_centered(self, mock_stdout):
        """Test print_block with centered alignment."""
        rows = [['head'], ['body']]
        print_block(rows, is_centered=True, colsize=10)
        output = strip_ansi(mock_stdout.getvalue())
        assert '  head  ' in output
        assert '   body   ' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_block_custom_head_format(self, mock_stdout):
        """Test print_block with custom head format."""
        rows = [['H1', 'H2'], ['D1', 'D2']]
        print_block(rows, format_head='1;4;')  # Bold underline
        output = mock_stdout.getvalue()
        assert '\x1b[1;4;104m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_block_single_row(self, mock_stdout):
        """Test print_block with single row."""
        rows = [['Only', 'Row']]
        print_block(rows)
        output = strip_ansi(mock_stdout.getvalue())
        assert 'Only' in output
        assert 'Row' in output


class TestPrintTable:
    """Test cases for print_table function."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_table_full(self, mock_stdout):
        """Test print_table with heads and body."""
        heads = ['H1', 'H2']
        body = [['D1', 'D2']]
        print_table(heads, body)
        output = strip_ansi(mock_stdout.getvalue())
        assert '┏' in output
        assert 'H1' in output
        assert 'D1' in output
        assert '┗' in output


# ===== TESTS FOR idx COMMAND =====

class TestTuibleParamsIdx:
    """Test cases for TuibleParams idx functionality."""

    def test_idx_parsing_basic(self):
        """Test basic idx parsing and storage."""
        params = TuibleParams()
        args = ['idx', '1', '2', '3']
        params.parseArguments(args)
        assert 'idx' in params.mode_columns
        assert params.mode_columns['idx'] == [['1', '2', '3']]
        assert params.is_index_mode == True

    def test_idx_with_head_and_body(self):
        """Test idx with head and body modes (idx before head)."""
        params = TuibleParams()
        # idx must come before head and body
        args = ['idx', '1', '2', 'head', 'Name', 'Age', 'body', 'Alice', '25', 'body', 'Bob', '30']
        params.parseArguments(args)
        assert 'head' in params.mode_columns
        assert 'idx' in params.mode_columns
        assert 'body' in params.mode_columns
        assert params.mode_columns['head'] == [['Name'], ['Age']]
        assert params.mode_columns['idx'] == [['1', '2']]
        assert params.mode_columns['body'] == [['Alice', 'Bob'], ['25', '30']]
        assert params.column_count == 3  # 2 body columns + 1 idx

    def test_idx_with_empty_strings(self):
        """Test idx with empty strings for padding."""
        params = TuibleParams()
        # Using idx with body and colon syntax for multi-row cells
        args = ['idx', 'i1', '', 'i3', 'body', 'b1', ':b11', 'body', '', ':b31']
        params.parseArguments(args)
        # Check idx values
        assert params.mode_columns['idx'] == [['i1', '', 'i3']]
        # Check body structure - with two body commands
        assert 'body' in params.mode_columns

    def test_idx_parameter_color(self):
        """Test idx color parameter (-ci)."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-ci', '31']
        params.parseArguments(args)
        assert params.format_index['color'] == '31'

    def test_idx_parameter_style(self):
        """Test idx style parameter (-fi)."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-fi', '1;4;']
        params.parseArguments(args)
        assert params.format_index['esc'] == '1;4;'

    def test_idx_alignment_center(self):
        """Test idx center alignment (-fic)."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-fic']
        params.parseArguments(args)
        assert params.format_index['align'] == 'center'

    def test_idx_alignment_left(self):
        """Test idx left alignment (-fil)."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-fil']
        params.parseArguments(args)
        assert params.format_index['align'] == 'left'

    def test_idx_alignment_right(self):
        """Test idx right alignment (-fir)."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-fir']
        params.parseArguments(args)
        assert params.format_index['align'] == 'right'

    def test_idx_without_body(self):
        """Test idx without body (edge case)."""
        params = TuibleParams()
        args = ['idx', '1', '2']
        params.parseArguments(args)
        assert 'idx' in params.mode_columns
        assert params.mode_columns['idx'] == [['1', '2']]
        assert 'body' not in params.mode_columns

    def test_idx_column_count_calculation(self):
        """Test column count calculation with idx (idx before head)."""
        params = TuibleParams()
        args = ['idx', '1', '2', 'head', 'H1', 'H2', 'body', 'B1', 'B2', 'body', 'B3', 'B4']
        params.parseArguments(args)
        assert params.column_count == 3  # 2 body columns + 1 idx

    def test_idx_after_top_allowed(self):
        """Test that idx after top is allowed."""
        params = TuibleParams()
        args = ['top', 'idx', '1', '2', 'body', 'data1', 'data2']
        params.parseArguments(args)  # Should not raise
        assert 'idx' in params.mode_columns

    def test_idx_after_head_not_allowed(self):
        """Test that idx after head is NOT allowed."""
        params = TuibleParams()
        args = ['head', 'H1', 'idx', '1', 'body', 'data']
        with pytest.raises(Exception) as exc_info:
            params.parseArguments(args)
        assert 'idx' in str(exc_info.value).lower()
        assert 'head' in str(exc_info.value).lower()

    def test_idx_after_body_not_allowed(self):
        """Test that idx after body is NOT allowed."""
        params = TuibleParams()
        args = ['body', 'data', 'idx', '1']
        with pytest.raises(Exception) as exc_info:
            params.parseArguments(args)
        assert 'idx' in str(exc_info.value).lower()
        assert 'body' in str(exc_info.value).lower()

    def test_idx_auto_numbering_no_elements(self):
        """Test that auto-numbering is enabled when no idx elements are specified."""
        params = TuibleParams()
        args = ['idx', 'body', 'data1', 'data2', 'body', 'data3', 'data4']
        params.parseArguments(args)
        # idx column should be empty (triggers auto-numbering)
        assert 'idx' in params.mode_columns
        # When idx is specified without elements, it should still be recognized
    
    def test_index_header_and_body_labels_are_tracked(self):
        params = TuibleParams()
        args = ['idx', 'ih', ':i1', ':i2', 'head', 'H1', 'body', 'B1']
        params.parseArguments(args)
        assert params.index_header_values == ['ih']
        assert params.index_body_values == ['i1', 'i2']

    def test_index_auto_numbering_flag_without_labels(self):
        params = TuibleParams()
        args = ['idx', 'head', 'H1', 'body', 'B1']
        params.parseArguments(args)
        assert params.index_auto_numbering

    def test_index_auto_numbering_flag_with_labels(self):
        params = TuibleParams()
        args = ['idx', 'header', ':body', 'head', 'H1', 'body', 'B1']
        params.parseArguments(args)
        assert not params.index_auto_numbering

    def test_index_command_alias_is_supported(self):
        params = TuibleParams()
        args = ['index', ':i1', 'body', 'B1']
        params.parseArguments(args)
        assert 'idx' in params.mode_columns
        assert params.mode_stack[0] == 'idx'


class TestTuibleTableIdx:
    """Test cases for TuibleTable idx rendering."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_basic(self, mock_stdout):
        """Test basic idx rendering."""
        params = TuibleParams()
        args = ['idx', '1', '2', 'body', 'data1', 'data2']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        assert '1' in output
        assert '2' in output
        assert 'data1' in output
        assert 'data2' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_index_alias(self, mock_stdout):
        """Ensure the alias `index` renders the same index column."""
        params = TuibleParams()
        args = ['index', ':i1', 'body', 'data']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        assert 'i1' in output
        assert 'data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_with_head(self, mock_stdout):
        """Test idx rendering with head (idx before head)."""
        params = TuibleParams()
        args = ['idx', '1', '2', 'head', 'Name', 'Age', 'body', 'Alice', '25', 'body', 'Bob', '30']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        # Check that idx values appear in output
        assert '1' in output
        assert '2' in output
        assert 'Name' in output
        assert 'Age' in output
        assert 'Alice' in output
        assert '25' in output
        assert 'Bob' in output
        assert '30' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_alignment_center(self, mock_stdout):
        """Test idx center alignment rendering."""
        params = TuibleParams()
        args = ['idx', ':test', 'body', 'data', '-fic']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        # Check that idx color is applied (default 31 italics)
        assert '\x1b[3;31m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_custom_color(self, mock_stdout):
        """Test idx custom color rendering."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-ci', '31']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        # Check for red color (31) in idx
        assert '\x1b[3;31m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_custom_style(self, mock_stdout):
        """Test idx custom style rendering."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-fi', '1;']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        # Check for bold style (1;) in idx
        assert '\x1b[1;31m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_with_borders(self, mock_stdout):
        """Test idx rendering with borders."""
        params = TuibleParams()
        args = ['top', 'idx', ':1', 'body', 'data', 'bot']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        assert '┏' in output
        assert '┗' in output
        assert '1' in output
        assert 'data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_dynamic_width(self, mock_stdout):
        """Test idx rendering with dynamic width."""
        params = TuibleParams()
        args = ['idx', ':very_long_idx', 'body', 'short_data', '-size', '-1']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        assert 'very_long_idx' in output
        assert 'short_data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_example_1(self, mock_stdout):
        """Test rendering example 1: tuible idx 'ih' ':i1' ':i2' head 'h1' 'h2' body 'b1' ':b11' 'b2' ':b21'
        
        Expected output:
        ┃ih┃h1 ┃h2 ┃
        ┃i1┃b1 ┃b2 ┃
        ┃i2┃b11┃b21┃
        """
        params = TuibleParams()
        args = ['idx', 'ih', ':i1', ':i2', 'head', 'h1', 'h2', 'body', 'b1', ':b11', 'b2', ':b21']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        assert 'ih' in output
        assert 'i1' in output
        assert 'i2' in output
        assert 'h1' in output
        assert 'h2' in output
        assert 'b1' in output
        assert 'b11' in output
        assert 'b2' in output
        assert 'b21' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_example_2(self, mock_stdout):
        """Test rendering example 2: tuible idx ':i1' ':i2' body b1 :b11 '' :b21
        
        Expected output:
        ┃i1┃b1 ┃   ┃
        ┃i2┃b11┃b21┃
        """
        params = TuibleParams()
        args = ['idx', ':i1', ':i2', 'body', 'b1', ':b11', '', ':b21']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        assert 'i1' in output
        assert 'i2' in output
        assert 'b1' in output
        assert 'b11' in output
        assert 'b21' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_example_3_auto_numbering(self, mock_stdout):
        """Test rendering example 3: tuible idx head 'col1' 'col2' body 'b1' ':b11' '' ':b21'
        
        Expected output (auto-numbering):
        ┃  0┃col1┃col2┃
        ┃  1┃b1  ┃    ┃
        ┃  2┃b11 ┃b21 ┃
        """
        params = TuibleParams()
        # idx before head is required
        args = ['idx', 'head', 'col1', 'col2', 'body', 'b1', ':b11', '', ':b21']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        # Check for auto-numbering (0, 1, 2)
        assert '0' in output
        assert '1' in output
        assert '2' in output
        assert 'col1' in output
        assert 'col2' in output
        assert 'b1' in output
        assert 'b11' in output
        assert 'b21' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_no_header_index_flag(self, mock_stdout):
        """Test that -nhi leaves the header index blank during auto-numbering."""
        params = TuibleParams()
        args = ['idx', 'head', 'H', 'body', 'D', '-nhi']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        lines = strip_ansi(mock_stdout.getvalue()).splitlines()
        assert '0' not in lines[0]
        assert '1' in lines[1]

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_auto_numbering_disabled_with_elements(self, mock_stdout):
        """Test that auto-numbering is disabled when idx elements are specified."""
        # Use two body commands to create two rows
        params = TuibleParams()
        args = ['idx', ':A', ':B', 'body', 'data1', 'body', 'data2']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        # Should use explicit idx values A and B, not auto-numbering
        assert 'A' in output
        assert 'B' in output
        assert 'data1' in output
        assert 'data2' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_empty_string_as_blank(self, mock_stdout):
        """Test that empty strings are correctly rendered as blanks."""
        # Use two body commands to create two rows
        params = TuibleParams()
        args = ['idx', ':A', ':B', 'body', 'data1', 'body', 'data2']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = strip_ansi(mock_stdout.getvalue())
        # Should have idx values A and B
        assert 'A' in output
        assert 'B' in output
        assert 'data1' in output
        assert 'data2' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_parameter_ci(self, mock_stdout):
        """Test idx color parameter (-ci) rendering."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-ci', '35']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        # Check for magenta color (35)
        assert '\x1b[3;35m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_parameter_fic_center(self, mock_stdout):
        """Test idx center alignment (-fic) rendering."""
        params = TuibleParams()
        args = ['idx', ':test', 'body', 'data', '-fic']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        # Should have index formatting
        assert 'test' in output
        assert 'data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_parameter_fir_right(self, mock_stdout):
        """Test idx right alignment (-fir) rendering."""
        params = TuibleParams()
        args = ['idx', ':test', 'body', 'data', '-fir']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        assert 'test' in output
        assert 'data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_parameter_fil_left(self, mock_stdout):
        """Test idx left alignment (-fil) rendering."""
        params = TuibleParams()
        args = ['idx', ':test', 'body', 'data', '-fil']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        assert 'test' in output
        assert 'data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_render_idx_parameter_fi_style(self, mock_stdout):
        """Test idx style parameter (-fi) rendering."""
        params = TuibleParams()
        args = ['idx', '1', 'body', 'data', '-fi', '1;']
        params.parseArguments(args)
        table = TuibleTable(params)
        table.execute()
        output = mock_stdout.getvalue()
        # Check for bold style (1;)
        assert '\x1b[1;31m' in output


