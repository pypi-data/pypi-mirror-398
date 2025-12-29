"""Tuible parameters handling."""

import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any


@dataclass
class TuibleParams:
    """Tuible Parameters

    This class encapsulates all configuration parameters for Tuible table generation,
    including formatting options, column body structures, and command-line argument parsing.
    It provides static methods for creating instances from command-line arguments and
    environment variables, and instance methods for parsing and validating input.

    The class manages:
    - Table formatting (colors, borders, alignment)
    - Column body organization across different modes (head, body, borders)
    - Command-line argument processing
    - Environment variable support for default settings
    - Dynamic column width calculation
    """
    tuible_helptxt: str = """🎨 tuible - Beautiful CLI Table Builder
============================================
Create expressive CLI tables with colors, borders, and auto sizing in seconds.

🧭 Modes
-----------
   top        - draw the top border
   index/idx  - dedicate the first column to an index column (must come before head/body)
   head       - add header row(s)
   body       - add body row(s)
   bot        - draw the bottom border

⟶ index notes:
   • If you do not provide any labels after index/idx, rows auto-number (header rows start at 0,
     body rows begin at 1).
   • Provide plain labels (e.g. i1) for header rows, colon-prefixed labels (e.g. :i1) for body rows.
   • Use empty strings ('') to render blank placeholders without breaking the layout.

📦 Parameter Groups
--------------------
Index column formatting:
   -ci <color>  - ANSI color code for index text
   -fi <style>  - ANSI style codes (bold, underline, etc.)
   -fic         - center-align the index column
   -fil         - left-align the index column
   -fir         - right-align the index column (default)

Head & body formatting:
   -ch <color>  - header color
   -cb <color>  - body color
   -fh <style>  - header style
   -fb <style>  - body style
   -fhc/-fhl/-fhr - align headers (center/left/right)
   -fbc/-fbl/-fbr - align body text (center/left/right)

Layout & borders:
    -size <num>  - column width (-1 for dynamic sizing)
    -fe <chars>  - edge characters (8 chars: lr, tb, corners, middle)
    -nb          - hide left/right borders for a compact display
    -nhi         - hide the auto-generated header index when auto-numbering is enabled

------------------------
⚙️ Environment variables
------------------------
Prefix options with 'TUIBLE_' to set defaults (e.g., TUIBLE_ci=35 for a magenta index).

📚 Index examples
-----------------
Example 1 - Header + body labels:
   tuible index 'ih' ':i1' ':i2' head 'h1' 'h2' body 'b1' ':b11' 'b2' ':b21'
   ┃ih┃h1 ┃h2 ┃
   ┃i1┃b1 ┃b2 ┃
   ┃i2┃b11┃b21┃

Example 2 - Body-only labels:
   tuible idx ':i1' ':i2' body b1 :b11 '' :b21
   ┃i1┃b1 ┃   ┃
   ┃i2┃b11┃b21┃

Example 3 - Auto-numbering:
   tuible index head 'col1' 'col2' body 'b1' ':b11' '' ':b21'
   ┃  0┃col1┃col2┃
   ┃  1┃b1  ┃    ┃
   ┃  2┃b11 ┃b21 ┃

Usage: tuible [options] <mode> [<mode arguments>] ... [options]
Use -h or --help for this message.
"""

    mode_columns:   Dict[str, List[List[str]]] = field(default_factory=dict)
    alone_args:     List[str]       = field(default_factory=lambda: ["-fhc", "-fhl", "-fhr", "-fbc",
                                                                      "-fbl", "-fbr", "-fic", "-fil", "-fir",
                                                                      "-nhi", "-nb", "-h", "--help"])
    mode_stack:     List[str]       = field(default_factory=list)
    columns:        List[List[str]] = field(default_factory=list)
    current_mode:   str             = ""
    is_index_mode:  bool            = False
    body:           List            = field(default_factory=list)
    size:           int             = 19
    column_count:   Optional[int]   = None
    column_widths:  List[int]       = field(default_factory=list)
    no_border:      bool            = False
    format_head:  Dict            = field(default_factory=lambda: {
                                      'color': '104', 'esc': '1;3;4;', 'align': 'center' })
    format_body:    Dict            = field(default_factory=lambda: {
                                      'color': '96', 'esc': '', 'align': 'left' })
    format_edge:    Dict            = field(default_factory=lambda: {
                                       'color': '93', 'symbol_leftright': '┃', 'symbol_topbottom': '━',
                                       'symbol_topleft': '┏', 'symbol_topright': '┓', 'symbol_bottomleft': '┗',
                                       'symbol_bottomright': '┛', 'symbol_topmiddle': '┳', 'symbol_bottommiddle': '┻' })
    format_index:   Dict            = field(default_factory=lambda: {
                                          'color': '31', 'esc': '3;', 'align': 'right', 'size': 3 })
    no_header_index: bool            = False
    index_header_values: List[str] = field(default_factory=list)
    index_body_values:   List[str] = field(default_factory=list)
    index_auto_numbering: bool       = False
    


    @staticmethod
    def print_help() -> None:
        """Print help information for the tuible application."""
        print(TuibleParams.tuible_helptxt)
    
    @classmethod
    def createFromArguments(cls) -> Optional["TuibleParams"]:
        """Create TuibleParams from command line arguments and environment variables."""
        sys_argv = sys.argv[1:]
        os_env = os.environ.items()

        # check for help
        if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
            cls.print_help()
            return None

        # check minimum arguments - at least one mode must be present
        mode_found = False
        i = 0
        while i < len(sys_argv):
            arg = sys_argv[i]
            if arg.startswith('-'):
                # Skip option and its value (if not a standalone option)
                if arg not in ["-fhc", "-fhl", "-fhr", "-fbc", "-fbl", "-fbr", "-fic", "-fil", "-fir", "-nb", "-h", "--help"]:
                    i += 2  # skip option and value
                else:
                    i += 1  # skip standalone option
            else:
                # Found a non-option argument
                if arg in ["body", "head", "top", "bot", "idx", "index"]:
                    mode_found = True
                    break
                i += 1
        
        if not mode_found:
            print("Usage: tuible body|head|top|bot|idx|index [body...] [options]")
            return None

        params = cls()

        # Parse environment variables
        env_prefix = 'TUIBLE_'
        env_argv = []
        for env_var, value in os_env:
            if env_var.startswith(env_prefix):
                param_name = env_var[len(env_prefix):].lower()
                env_argv.append('-'+param_name)
                if '-'+param_name not in params.alone_args:
                    env_argv.append(value)
        
        # Combine environment args with command line args
        combined_argv = env_argv + sys_argv
        params.parseArguments(combined_argv)

        return params
    
    def parseArguments(self, args: List[str]) -> None:
        """Parse a list of arguments to populate the TuibleParams fields."""
        i, self.col_pos = 0, -1
       
        while i < len(args):
            arg = args[i]
            if not arg.startswith('-'):
                # Handle commands and items
                valid_modes = ["body", "head", "top", "bot", "idx", "index"]
                
                if arg in valid_modes:
                    # It's a command/mode switch
                    canonical = 'idx' if arg == 'index' else arg
                    self.current_mode = canonical
                    self._validateCommandPosition(self.current_mode)
                    self.mode_stack.append(self.current_mode)
                    self.is_index_mode = (self.current_mode == 'idx')

                    if self.current_mode not in self.mode_columns:
                        self.mode_columns[self.current_mode] = []
                    
                    self.columns = self.mode_columns[self.current_mode]
                    self.col_pos = -1 # reset column position
                    if self.current_mode == 'idx':
                        self.index_auto_numbering = True
                        self.index_header_values.clear()
                        self.index_body_values.clear()
                else:
                    # It's an item for the current mode
                    if self.current_mode == '':
                        raise Exception(f"First argument must be one of {', '.join(valid_modes)}, got: {arg}")
                    
                    self._extractItems([arg])
            else:
                # It's a parameter
                param_len = self._extractParameters(args[i:])
                i += param_len - 1 # -1 because the loop will increment i
            
            i += 1
        
        # Set column count if not explicitly set - use max column count from all modes
        if self.column_count is None:
            max_cols = 0
            for mode, columns in self.mode_columns.items():
                if mode == 'idx':
                    # idx is a single column prepended to body
                    continue
                max_cols = max(max_cols, len(columns))
            # If idx is present, add 1 for the idx column
            if 'idx' in self.mode_columns:
                max_cols += 1
            if max_cols > 0:
                self.column_count = max_cols
        
        # Ensure all modes have the same number of columns (add empty columns if needed)
        if self.column_count:
            for mode, columns in self.mode_columns.items():
                if mode == 'idx':
                    # idx is special, don't add empty columns
                    continue
                target_cols = self.column_count - (1 if 'idx' in self.mode_columns else 0)
                while len(columns) < target_cols:
                    columns.append([])  # add empty column
        
        # After parsing: fill all columns for each mode to the same height
        for mode, columns in self.mode_columns.items():
            if columns:
                max_rows = max(len(col) for col in columns) if columns else 0
                for col in columns:
                    while len(col) < max_rows:
                        col.append("")  # fill with empty strings
    
    def _validateCommandPosition(self, command: str) -> None:
        """Validate that commands are in a valid order.
        
        Rules:
        - idx must not come after head or body
        - idx can come after top
        - idx must come before head/body/end (bot)
        """
        if command != 'idx':
            return
        
        # Check if any 'head' or 'body' command was already used
        if 'head' in self.mode_stack or 'body' in self.mode_stack:
            raise Exception("'idx' command must come before 'head' or 'body' commands")
    
    def _extractItems(self, args: List[str]) -> bool:
        """Extract items for the current mode. Returns True if an item was processed."""
        arg = args[0]

        # index mode handles labels differently
        if self.is_index_mode:
            if len(self.columns) == 0:
                self.columns.append([])

            if arg.startswith(':'):
                value = arg[1:] if len(arg) > 1 else ""
                self.index_body_values.append(value)
            else:
                value = arg
                self.index_header_values.append(value)

            self.columns[0].append(value)
            self.index_auto_numbering = False
            return True

        # handle continuation in current column (starts with ':')
        if arg.startswith(':'):
            if self.col_pos < 0:
                raise Exception('":" not allowed before any column is started')
            # remove ':' prefix and add to current column
            self.columns[self.col_pos].append(arg[1:] if len(arg) > 1 else "")
        
        # handle single space " " as empty column start
        elif arg == " ":
            self.col_pos += 1
            if self.col_pos >= len(self.columns):
                self.columns.append([])
            self.columns[self.col_pos].append("")
        
        # handle normal text (starts a new column in head/body mode)
        else:
            self.col_pos += 1
            if self.col_pos >= len(self.columns):
                self.columns.append([])
            self.columns[self.col_pos].append(arg)
        return True

    def _extractParameters(self, args: List[str]) -> int:
        """Extract parameters and return the number of arguments consumed."""
        arg = args[0]
        
        # Handle standalone arguments (no value needed)
        if arg in self.alone_args:
            if arg == '-nb':
                self.no_border = True
            elif arg == '-nhi':
                self.no_header_index = True
            elif arg == '-fhc':
                self.format_head['align'] = 'center'
            elif arg == '-fhl':
                self.format_head['align'] = 'left'
            elif arg == '-fhr':
                self.format_head['align'] = 'right'
            elif arg == '-fbc':
                self.format_body['align'] = 'center'
            elif arg == '-fbl':
                self.format_body['align'] = 'left'
            elif arg == '-fbr':
                self.format_body['align'] = 'right'
            elif arg == '-fic':
                self.format_index['align'] = 'center'
            elif arg == '-fil':
                self.format_index['align'] = 'left'
            elif arg == '-fir':
                self.format_index['align'] = 'right'
            return 1  # consumed 1 argument
        else:
            # Handle parameters that require a value
            if len(args) < 2:
                raise Exception(f"Parameter {arg} requires a value.")
            value = args[1]
            
            if arg == '-ce':      # edge color
                self.format_edge['color'] = value
            elif arg == '-cb':    # body color
                self.format_body['color'] = value
            elif arg == '-ch':    # head color
                self.format_head['color'] = value
            elif arg == '-ci':    # index color
                self.format_index['color'] = value
            elif arg == '-fb':    # body format/escape codes
                self.format_body['esc'] = value
            elif arg == '-fh':    # head format/escape codes
                self.format_head['esc'] = value
            elif arg == '-fi':    # index format/escape codes
                self.format_index['esc'] = value
            elif arg == '-fe':    # edge characters (8 chars expected)
                if len(value) >= 8:
                    self.format_edge['symbol_leftright'] = value[0]
                    self.format_edge['symbol_topbottom'] = value[1]
                    self.format_edge['symbol_topleft'] = value[2]
                    self.format_edge['symbol_topright'] = value[3]
                    self.format_edge['symbol_bottomleft'] = value[4]
                    self.format_edge['symbol_bottomright'] = value[5]
                    self.format_edge['symbol_topmiddle'] = value[6]
                    self.format_edge['symbol_bottommiddle'] = value[7]
            elif arg == '-size':  # column width
                self.size = int(value)
            else:
                print(f"Warning: Unknown parameter {arg}")
            
            return 2  # consumed 2 arguments (parameter + value)
