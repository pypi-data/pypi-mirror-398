"""CLI interface for tuible."""

import sys
from .params import CliTableParams
from .table import CliTable


def main():
    """Main CLI entry point for tuible."""
    try:
        params = CliTableParams.createFromArguments()
        if params:
            table = CliTable(params)
            table.execute()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
