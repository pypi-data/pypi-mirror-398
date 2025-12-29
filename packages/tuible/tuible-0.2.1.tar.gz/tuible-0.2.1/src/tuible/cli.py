"""CLI interface for tuible."""

import sys
from .params import TuibleParams
from .table import TuibleTable


def main():
    """Main CLI entry point for tuible."""
    try:
        params = TuibleParams.createFromArguments()
        if params:
            table = TuibleTable(params)
            table.execute()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
