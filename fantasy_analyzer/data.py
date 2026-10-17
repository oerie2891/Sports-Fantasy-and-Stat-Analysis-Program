"""
=============================================================================
 DATA LOADING  (fantasy_analyzer/data.py)
=============================================================================
 PURPOSE
   Reads a CSV file of per-game player stats and turns each row into a
   GameLog object the rest of the program can work with.

 CONTENTS
   1. Column rules  - which CSV columns are required / treated as labels
   2. GameLog       - one player's stats for one game
   3. load_game_logs() - read and validate the CSV

 EXPECTED CSV
   Columns: player, position, week, plus any stat columns.
   An optional `team` column is carried through. Blank stat cells count as 0.
=============================================================================
"""

import csv
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# SECTION 1: COLUMN RULES
# REQUIRED columns must exist. META columns are labels, not stats; every
# other column is treated as a numeric stat.
# ---------------------------------------------------------------------------
REQUIRED = ("player", "position", "week")
META = {"player", "position", "team", "week"}


# ---------------------------------------------------------------------------
# SECTION 2: GAME LOG
# One row of the CSV: who played, which week, and their raw stats.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GameLog:
    player: str
    position: str
    team: str
    week: int
    stats: dict[str, float]  # stat column -> value, e.g. {"rush_yds": 87.0}


# ---------------------------------------------------------------------------
# SECTION 3: CSV LOADER
# Reads the file, checks the required columns exist, converts numbers, and
# reports the exact line number if a row can't be read.
# ---------------------------------------------------------------------------
def load_game_logs(path: str | Path) -> list[GameLog]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)

        # --- 3a. Validate header ----------------------------------------
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing required column(s): {', '.join(missing)}")

        # --- 3b. Convert each row into a GameLog ------------------------
        logs = []
        for line_no, row in enumerate(reader, start=2):  # line 1 is the header
            try:
                stats = {k: float(v) if v not in ("", None) else 0.0 for k, v in row.items() if k not in META}
                logs.append(
                    GameLog(
                        player=row["player"].strip(),
                        position=row["position"].strip().upper(),
                        team=(row.get("team") or "").strip(),
                        week=int(row["week"]),
                        stats=stats,
                    )
                )
            except ValueError as e:
                raise ValueError(f"{path}:{line_no}: {e}") from None
    return logs
