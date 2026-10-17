"""Load per-game player stat logs from CSV.

Expected columns: player, position, week, plus any stat columns.
An optional `team` column is carried through. Blank stat cells count as 0.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

REQUIRED = ("player", "position", "week")
META = {"player", "position", "team", "week"}


@dataclass(frozen=True)
class GameLog:
    player: str
    position: str
    team: str
    week: int
    stats: dict[str, float]


def load_game_logs(path: str | Path) -> list[GameLog]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing required column(s): {', '.join(missing)}")
        logs = []
        for line_no, row in enumerate(reader, start=2):
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
