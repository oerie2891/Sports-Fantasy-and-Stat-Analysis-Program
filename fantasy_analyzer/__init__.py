"""
=============================================================================
 PACKAGE INTERFACE  (fantasy_analyzer/__init__.py)
=============================================================================
 PURPOSE
   Defines what `import fantasy_analyzer` gives you, so the library can be
   used from your own scripts without the command line:

       from fantasy_analyzer import load_game_logs, get_scoring, analyze
       reports = analyze(load_game_logs("my.csv"), get_scoring("nfl-ppr"))
=============================================================================
"""

from .analysis import PlayerReport, analyze, find_player
from .data import GameLog, load_game_logs
from .scoring import PRESETS, ScoringSystem, get_scoring

# ---------------------------------------------------------------------------
# PUBLIC API: the names available to `from fantasy_analyzer import *`
# ---------------------------------------------------------------------------
__all__ = ["GameLog", "PRESETS", "PlayerReport", "ScoringSystem", "analyze", "find_player", "get_scoring", "load_game_logs"]
