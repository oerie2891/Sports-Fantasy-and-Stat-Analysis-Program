"""Scoring systems: map raw stat columns to fantasy points."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringSystem:
    name: str
    points: dict[str, float]
    # Default league shape used for replacement-level calculations.
    starters: dict[str, int] = field(default_factory=dict)
    teams: int = 12

    def score(self, stats: dict[str, float]) -> float:
        return round(sum(stats.get(stat, 0.0) * pts for stat, pts in self.points.items()), 2)


_NFL_BASE = {
    "pass_yds": 0.04,
    "pass_td": 4,
    "int": -2,
    "rush_yds": 0.1,
    "rush_td": 6,
    "rec_yds": 0.1,
    "rec_td": 6,
    "fumbles_lost": -2,
    "two_pt": 2,
}
_NFL_STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}

PRESETS: dict[str, ScoringSystem] = {
    "nfl-standard": ScoringSystem("NFL Standard", {**_NFL_BASE, "rec": 0.0}, _NFL_STARTERS),
    "nfl-half-ppr": ScoringSystem("NFL Half PPR", {**_NFL_BASE, "rec": 0.5}, _NFL_STARTERS),
    "nfl-ppr": ScoringSystem("NFL PPR", {**_NFL_BASE, "rec": 1.0}, _NFL_STARTERS),
    "nba-points": ScoringSystem(
        "NBA Points",
        {"pts": 1, "reb": 1.2, "ast": 1.5, "stl": 3, "blk": 3, "tov": -1, "fg3m": 0.5},
        {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1},
        teams=12,
    ),
}


def get_scoring(name: str) -> ScoringSystem:
    try:
        return PRESETS[name]
    except KeyError:
        raise ValueError(f"Unknown scoring preset '{name}'. Choose from: {', '.join(PRESETS)}") from None
