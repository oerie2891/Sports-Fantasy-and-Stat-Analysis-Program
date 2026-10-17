"""
=============================================================================
 LAUNCHER  (fantasy_analyzer/__main__.py)
=============================================================================
 PURPOSE
   Runs when you type `python -m fantasy_analyzer`. Hands control to the
   command-line interface and passes its exit code back to the shell.
=============================================================================
"""

import sys

from .cli import main

sys.exit(main())
