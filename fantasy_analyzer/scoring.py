"""
=============================================================================
 SCORING  (fantasy_analyzer/scoring.py)
=============================================================================
 PURPOSE
   Converts raw stats (yards, touchdowns, rebounds...) into fantasy points.

 CONTENTS
   1. ScoringSystem  - the rules for one scoring format
   2. Presets        - ready-made formats (NFL standard/half/full PPR, NBA)
   3. get_scoring()  - look up a preset by name

 HOW TO ADD YOUR OWN LEAGUE'S SCORING
   Copy one of the entries in PRESETS (section 2), give it a new key, and
   change the points-per-stat numbers. The key becomes a --scoring option.
=============================================================================
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# SECTION 1: SCORING SYSTEM
# One scoring format: points awarded per unit of each stat, plus the league
# shape (teams and starters per position) used to work out replacement level.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ScoringSystem:
    name: str
    points: dict[str, float]  # stat column -> points per unit, e.g. {"rush_td": 6}
    # Default league shape used for replacement-level calculations.
    starters: dict[str, int] = field(default_factory=dict)
    teams: int = 12

    def score(self, stats: dict[str, float]) -> float:
        """Fantasy points for one game. Stats the format doesn't use are ignored."""
        return round(sum(stats.get(stat, 0.0) * pts for stat, pts in self.points.items()), 2)


# ---------------------------------------------------------------------------
# SECTION 2: PRESETS
# Built-in scoring formats. The three NFL formats share the same base rules
# and differ only in points per reception ("rec").
# ---------------------------------------------------------------------------

# --- 2a. NFL shared rules -------------------------------------------------
_NFL_BASE = {
    "pass_yds": 0.04,  # 1 point per 25 passing yards
    "pass_td": 4,
    "int": -2,
    "rush_yds": 0.1,  # 1 point per 10 rushing yards
    "rush_td": 6,
    "rec_yds": 0.1,  # 1 point per 10 receiving yards
    "rec_td": 6,
    "fumbles_lost": -2,
    "two_pt": 2,
}
_NFL_STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}

# --- 2b. Preset table (key = the --scoring option name) -------------------
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


# ---------------------------------------------------------------------------
# SECTION 3: PRESET LOOKUP
# ---------------------------------------------------------------------------
def get_scoring(name: str) -> ScoringSystem:
    """Return the preset called `name`, or raise a clear error listing valid names."""
    try:
        return PRESETS[name]
    except KeyError:
        raise ValueError(f"Unknown scoring preset '{name}'. Choose from: {', '.join(PRESETS)}") from None
