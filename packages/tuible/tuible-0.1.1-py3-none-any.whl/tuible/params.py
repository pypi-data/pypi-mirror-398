"""CLI Table Parameters handling."""

import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union


@dataclass
class CliTableParams:
    """CLI Table Parameters

    This class encapsulates all configuration parameters for CLI table generation,
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
    clitable_helptxt: str = """CliTable - Simple table output CLI application
==============================================
Usage: tuible [options] <mode> [<body>] [options] [<mode> [<body>] ...] [options]

Modes:
  body    - Print body line
  head  - Print head line
  top     - Print top border
  bot  - Print bottom border

Options:
  -ce <color>  - Set edge color (e.g., 34 for blue)
  -cb <color>  - Set body color (e.g., 32 for green)
  -ch <color>  - Set head color (e.g., 33 for yellow)
  -fb <style>  - Set body style (e.g., 4 for underline)
  -fh <style>  - Set head style (e.g., 4 for underline)
  -fe <chars>  - Set edge characters (8 chars: left-right, top-bottom, corners, middle)
                  Default: '┃━┏┓┗┛┳┻'
  -size <num>  - Set column width (default: 19)
                  Use -1 for dynamic width based on content
  -cc <num>    - Set column count
  -fhc         - Set head alignment to center
  -fhl         - Set head alignment to left
  -fhr         - Set head alignment to right
  -fbc         - Set body alignment to center
  -fbl         - Set body alignment to left
  -fbr         - Set body alignment to right
  -nb          - No border (left and right)
  -h, --help   - Show this help message

Symbol Sets:
  Default edge symbols: "┃━┏┓┗┛┳┻"
  Other symbol sets:    "│─┌┐└┘┬┴", "║═╔╗╚╝╦╩", "│─╭╮╰╯┬┴", "┆┄┌┐└┘┬┴", "┇┉┏┓┗┛┳┻" 

Environment Variables:
All parameters can also be set as environment variables. 
The variable name must start with 'CLITABLE_', followed by the parameter. 
For example, 
  "export CLITABLE_fb='1;3;4;'" 
has the same effect as passing the parameter directly when calling the function, like this: 
  "-fb '1;3;4;'"

Example:
  export CLITABLE_fe='║═╔╗╚╝╦╩'
  tuible top head 'title 1' 'title 2' body 'body 1' 'body 2' bot
"""
    mode_columns:   Dict[str, List[List[str]]] = field(default_factory=dict)
    alone_args:     List[str]       = field(default_factory=lambda: ["-fhc", "-fhl", "-fhr", "-fbc", 
                                                                     "-fbl", "-fbr", "-nb", "-h", "--help"])
    mode_stack:     List[str]       = field(default_factory=list)
    columns:        List[List[str]] = field(default_factory=list)
    current_mode:   str             = ""
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
    
    @staticmethod
    def print_help() -> None:
        """Print help information for the tuible application."""
        print(CliTableParams.clitable_helptxt)
    
    @classmethod
    def createFromArguments(cls) -> Optional["CliTableParams"]:
        """Create CliTableParams from command line arguments and environment variables."""
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
            if arg[0] == '-':
                # Skip option and its value (if not a standalone option)
                if arg not in ["-fhc", "-fhl", "-fhr", "-fbc", "-fbl", "-fbr", "-nb", "-h", "--help"]:
                    i += 2  # skip option and value
                else:
                    i += 1  # skip standalone option
            else:
                # Found a non-option argument
                if arg in ["body", "head", "top", "bot"]:
                    mode_found = True
                    break
                i += 1
        
        if not mode_found:
            print("Usage: tuible body|head|top|bot [body...] [options]")
            return None

        params = cls()

        # Parse environment variables
        env_prefix = 'CLITABLE_'
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
        """Parse a list of arguments to populate the CliTableParams fields."""
        i, self.col_pos = 0, -1
       
        while i < len(args):
            # treat command or item
            if args[i][0] != '-':

                # first none-'-'-parameter must be in ["body", "head", "top", "bot"]
                if self.current_mode == '' and args[i] not in ["body", "head", "top", "bot"]:
                    raise Exception(f"First argument must be one of body|head|top|bot, got: {args[i]}")

                # handle commands and items (head/body)
                isItem = self._extractItems(args[i:])
                if not isItem: # no item means
                    self.current_mode = args[i] # is a command
                    self.mode_stack.append(self.current_mode)
                    
                    # Initialize columns list for this mode if needed
                    if self.current_mode not in self.mode_columns:
                        self.mode_columns[self.current_mode] = []
                    self.columns = self.mode_columns[self.current_mode]
                    
                    i += 1
                    self.col_pos = -1 # reset column position
                    continue
            else:
                param_len = self._extractParameters(args[i:])
                i += param_len
                continue

            # next argument
            i += 1
        
        # Set column count if not explicitly set - use max column count from all modes
        if self.column_count is None:
            max_cols = 0
            for columns in self.mode_columns.values():
                max_cols = max(max_cols, len(columns))
            if max_cols > 0:
                self.column_count = max_cols
        
        # Ensure all modes have the same number of columns (add empty columns if needed)
        if self.column_count:
            for mode, columns in self.mode_columns.items():
                while len(columns) < self.column_count:
                    columns.append([])  # add empty column
        
        # After parsing: fill all columns for each mode to the same height
        for mode, columns in self.mode_columns.items():
            if columns:
                max_rows = max(len(col) for col in columns) if columns else 0
                for col in columns:
                    while len(col) < max_rows:
                        col.append("")  # fill with empty strings
        
    def _extractItems(self, args: List[str]) -> bool:
        arg = args[0]
        if arg in ["body", "head", "top", "bot"]: return False

        # handle body argument starting with ':' (continuation in current column)
        if arg[0] == ':':
            # check if we have a valid current column
            if self.col_pos < 0:
                raise Exception('":" not allowed before any column is started')
            # remove ':' prefix and add to current column (empty string if just ':')
            self.columns[self.col_pos].append(arg[1:] if len(arg) > 1 else "")
        
        # handle single space " " as empty column start
        elif arg == " ":
            self.col_pos += 1
            # create new column if needed
            if self.col_pos >= len(self.columns):
                self.columns.append([])
            # add empty string to start empty column
            self.columns[self.col_pos].append("")
        
        # handle body as first item of its column (normal text)
        else:
            self.col_pos += 1
            # create new column if needed
            if self.col_pos >= len(self.columns):
                self.columns.append([])
            # add element to current column
            self.columns[self.col_pos].append(arg)
        return True

    def _extractParameters(self, args: List[str]) -> int:
        """Extract parameters and return the number of arguments consumed."""
        arg = args[0]
        
        # Handle standalone arguments (no value needed)
        if arg in self.alone_args:
            if arg == '-nb':
                self.no_border = True
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
            elif arg == '-fb':    # body format/escape codes
                self.format_body['esc'] = value
            elif arg == '-fh':    # head format/escape codes
                self.format_head['esc'] = value
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
            elif arg == '-cc':    # column count
                self.column_count = int(value)
            else:
                print(f"Warning: Unknown parameter {arg}")
            
            return 2  # consumed 2 arguments (parameter + value)
