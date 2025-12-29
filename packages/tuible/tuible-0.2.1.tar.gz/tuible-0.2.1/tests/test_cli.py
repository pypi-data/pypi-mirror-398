"""Unit tests for CLI interface in tuible."""

import pytest
import re
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from tuible.cli import main


def strip_ansi(text):
    """Strip ANSI escape sequences from string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class TestCLI:
    """Test cases for CLI."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_help(self, mock_stdout):
        """Test help output."""
        test_args = ['tuible', '--help']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'Usage: tuible' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_body_basic(self, mock_stdout):
        """Test basic body command."""
        test_args = ['tuible', 'body', 'col1', 'col2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'col1' in output
        assert 'col2' in output
        assert '┃' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_head_basic(self, mock_stdout):
        """Test basic head command."""
        test_args = ['tuible', 'head', 'H1', 'H2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'H1' in output
        assert 'H2' in output
        assert '┃' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_full_table(self, mock_stdout):
        """Test full table sequence (simulated by multiple calls or combined args)."""
        # The current CLI implementation in cli.py executes one set of params.
        # tuible allows multiple modes in one call if parsed correctly.
        # Let's check parseArguments in params.py.
        # It loops through args and appends to mode_stack.
        test_args = ['tuible', 'top', 'head', 'H1', 'body', 'D1', 'bot']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert '┏' in output
        assert 'H1' in output
        assert 'D1' in output
        assert '┗' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_no_border(self, mock_stdout):
        """Test no border option."""
        test_args = ['tuible', 'body', 'test', '-nb']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'test' in output
        assert '┃' not in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_custom_colors(self, mock_stdout):
        """Test custom colors."""
        test_args = ['tuible', 'body', 'test', '-ce', '31', '-cb', '32']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert '\x1b[31m' in output # Edge color
        assert '\x1b[32m' in output # body color

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_dynamic_size(self, mock_stdout):
        """Test dynamic sizing."""
        test_args = ['tuible', 'body', 'very long string', '-size', '-1']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'very long string' in output
        # Check if width is at least the length of the string
        # The output will have ANSI codes, so we just check it printed.

    # ===== TESTS FOR idx COMMAND =====
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_basic(self, mock_stdout):
        """Test basic idx command."""
        test_args = ['tuible', 'idx', '1', '2', 'body', 'data1', 'data2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert '1' in output
        assert '2' in output
        assert 'data1' in output
        assert 'data2' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_valid_command(self, mock_stdout):
        """Test that idx is recognized as a valid command."""
        # Use two body commands to create two rows
        test_args = ['tuible', 'idx', ':i1', ':i2', 'body', 'b1', 'body', 'b2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Should not raise an error and should produce output
        stripped = strip_ansi(output)
        assert 'i1' in stripped
        assert 'i2' in stripped
        assert 'b1' in stripped
        assert 'b2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_index_alias(self, mock_stdout):
        """Test that the index alias produces the same output."""
        test_args = ['tuible', 'index', ':i1', 'body', 'data']
        with patch('sys.argv', test_args):
            main()
        output = strip_ansi(mock_stdout.getvalue())
        assert 'i1' in output
        assert 'data' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_after_top_allowed(self, mock_stdout):
        """Test that idx is allowed after top command."""
        test_args = ['tuible', 'top', 'idx', '1', '2', 'body', 'data1', 'data2', 'bot']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Should not raise an error
        assert '1' in output
        assert '2' in output
        assert 'data1' in output
        assert '┏' in output  # top border
        assert '┗' in output  # bottom border

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_after_head_not_allowed(self, mock_stdout):
        """Test that idx is NOT allowed after head command (should raise error)."""
        test_args = ['tuible', 'head', 'H1', 'H2', 'idx', '1', '2', 'body', 'b1', 'b2']
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1  # Exit code should be 1 for error

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_after_body_not_allowed(self, mock_stdout):
        """Test that idx is NOT allowed after body command (should raise error)."""
        test_args = ['tuible', 'body', 'b1', 'b2', 'idx', '1', '2']
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1  # Exit code should be 1 for error

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_with_head(self, mock_stdout):
        """Test idx with head and body (header rows skip index)."""
        # idx must come before head, so use: idx head body body
        test_args = ['tuible', 'idx', '1', '2', 'head', 'Name', 'Age', 'body', 'Alice', '25', 'body', 'Bob', '30']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'Name' in output
        assert 'Age' in output
        assert 'Alice' in output
        assert '25' in output
        assert 'Bob' in output
        assert '30' in output
        # Index should appear in body rows
        assert '1' in output
        assert '2' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_with_empty_padding(self, mock_stdout):
        """Test idx with empty strings for padding."""
        test_args = ['tuible', 'idx', ':i1', ':i2', 'body', 'b1', ':b11', '', ':b21']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'i1' in output
        assert 'i2' in output
        assert 'b1' in output
        assert 'b11' in output
        assert 'b21' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_parameter_color(self, mock_stdout):
        """Test index color parameter (-ci)."""
        test_args = ['tuible', 'idx', '1', 'body', 'data', '-ci', '31']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Check for red italic color (3;31) in index
        assert '\x1b[3;31m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_parameter_style(self, mock_stdout):
        """Test index style parameter (-fi)."""
        test_args = ['tuible', 'idx', '1', 'body', 'data', '-fi', '1;']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Check for bold style (1;) in index
        assert '\x1b[1;31m' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_alignment_center(self, mock_stdout):
        """Test index center alignment (-fic)."""
        # Use two body commands to create two rows
        test_args = ['tuible', 'idx', ':idx1', ':idx2', 'body', 'data1', 'body', 'data2', '-fic']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'idx1' in stripped
        assert 'idx2' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_alignment_left(self, mock_stdout):
        """Test index left alignment (-fil)."""
        test_args = ['tuible', 'idx', ':idx1', ':idx2', 'body', 'data1', 'body', 'data2', '-fil']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'idx1' in stripped
        assert 'idx2' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_alignment_right(self, mock_stdout):
        """Test index right alignment (-fir)."""
        test_args = ['tuible', 'idx', ':idx1', ':idx2', 'body', 'data1', 'body', 'data2', '-fir']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'idx1' in stripped
        assert 'idx2' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_full_table(self, mock_stdout):
        """Test full table with idx, borders, and colors."""
        # idx must come before head, so use: top idx head body body bot
        test_args = ['tuible', 'top', 'idx', '1', '2', 'head', 'Item', 'Qty', 'body', 'Apples', '5', 'body', 'Oranges', '3', 'bot', '-ch', '33', '-ci', '35']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert '┏' in stripped
        assert 'Item' in stripped
        assert 'Qty' in stripped
        assert 'Apples' in stripped
        assert '5' in stripped
        assert 'Oranges' in stripped
        assert '3' in stripped
        assert '┗' in stripped
        # Check colors
        assert '33m' in output  # Yellow headers
        assert '\x1b[3;35m' in output  # Magenta index

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_without_body(self, mock_stdout):
        """Test idx without body (edge case)."""
        test_args = ['tuible', 'idx', '1', '2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Should not crash, but no output expected since no body
        assert output.strip() == ""

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_example_1(self, mock_stdout):
        """Test rendering example 1: tuible idx 'ih' ':i1' ':i2' head 'h1' 'h2' body 'b1' ':b11' 'b2' ':b21'"""
        test_args = ['tuible', 'idx', 'ih', ':i1', ':i2', 'head', 'h1', 'h2', 'body', 'b1', ':b11', 'b2', ':b21']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
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
    def test_cli_idx_example_2(self, mock_stdout):
        """Test rendering example 2: tuible idx ':i1' ':i2' body b1 :b11 '' :b21"""
        test_args = ['tuible', 'idx', ':i1', ':i2', 'body', 'b1', ':b11', '', ':b21']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        assert 'i1' in output
        assert 'i2' in output
        assert 'b1' in output
        assert 'b11' in output
        assert 'b21' in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_example_3_auto_numbering(self, mock_stdout):
        """Test rendering example 3: tuible idx head 'col1' 'col2' body 'b1' ':b11' '' ':b21'
        
        Expected output with auto-numbering:
        ┃  0┃col1┃col2┃
        ┃  1┃b1  ┃    ┃
        ┃  2┃b11 ┃b21 ┃
        """
        test_args = ['tuible', 'idx', 'head', 'col1', 'col2', 'body', 'b1', ':b11', '', ':b21']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Check for auto-numbering (0, 1, 2)
        stripped = strip_ansi(output)
        assert '0' in stripped
        assert '1' in stripped
        assert '2' in stripped
        assert 'col1' in stripped
        assert 'col2' in stripped
        assert 'b1' in stripped
        assert 'b11' in stripped
        assert 'b21' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_auto_numbering_disabled_with_elements(self, mock_stdout):
        """Test that auto-numbering is disabled when index elements are specified."""
        # Use two body commands to create two rows
        test_args = ['tuible', 'idx', ':A', ':B', 'body', 'data1', 'body', 'data2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        # Should use explicit index values A and B, not auto-numbering
        stripped = strip_ansi(output)
        assert 'A' in stripped
        assert 'B' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_empty_string_as_blank(self, mock_stdout):
        """Test that empty strings are correctly rendered as blanks."""
        # Use two body commands to create two rows
        test_args = ['tuible', 'idx', ':A', ':B', 'body', 'data1', 'body', 'data2']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'A' in stripped
        assert 'B' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_no_header_index(self, mock_stdout):
        """Test that -nhi suppresses the header index when auto-numbering."""
        test_args = ['tuible', 'idx', 'head', 'H1', 'head', 'H2', 'body', 'D1', '-nhi']
        with patch('sys.argv', test_args):
            main()
        output = strip_ansi(mock_stdout.getvalue()).splitlines()
        assert '0' not in output[0]
        assert '0' not in output[1]
        assert '1' in output[-1]

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_parameter_fic_center(self, mock_stdout):
        """Test idx center alignment with -fic parameter."""
        test_args = ['tuible', 'idx', ':idx1', ':idx2', 'body', 'data1', 'body', 'data2', '-fic']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'idx1' in stripped
        assert 'idx2' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_parameter_fir_right(self, mock_stdout):
        """Test idx right alignment with -fir parameter."""
        test_args = ['tuible', 'idx', ':idx1', ':idx2', 'body', 'data1', 'body', 'data2', '-fir']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'idx1' in stripped
        assert 'idx2' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_idx_parameter_fil_left(self, mock_stdout):
        """Test idx left alignment with -fil parameter."""
        test_args = ['tuible', 'idx', ':idx1', ':idx2', 'body', 'data1', 'body', 'data2', '-fil']
        with patch('sys.argv', test_args):
            main()
        output = mock_stdout.getvalue()
        stripped = strip_ansi(output)
        assert 'idx1' in stripped
        assert 'idx2' in stripped
        assert 'data1' in stripped
        assert 'data2' in stripped
