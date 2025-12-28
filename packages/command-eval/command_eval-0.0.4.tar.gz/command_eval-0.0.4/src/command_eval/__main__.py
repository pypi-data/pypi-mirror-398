"""Main entry point for running command-eval as a module.

Usage: python -m command_eval [args]
"""

import sys

from command_eval.presentation.cli import main

if __name__ == "__main__":
    sys.exit(main())
