"""Unit tests for CLI interface in tuible."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from tuible.cli import main


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
        test_args = ['tuible', 'top', 'head', 'H1', 'body', 'D1', 'bot', '-cc', '1']
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
