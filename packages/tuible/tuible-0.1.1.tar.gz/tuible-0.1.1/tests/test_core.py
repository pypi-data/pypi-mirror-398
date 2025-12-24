"""Unit tests for core functions in tuible."""

import pytest
import re
from unittest.mock import patch, MagicMock
from io import StringIO
from tuible.core import print_line, print_block, print_table


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
