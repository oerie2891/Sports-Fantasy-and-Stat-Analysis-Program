"""
=============================================================================
 ANALYSIS ENGINE  (fantasy_analyzer/analysis.py)
=============================================================================
 PURPOSE
   The core of the program. Takes every game log, scores it, and builds a
   PlayerReport per player with all the performance metrics.

 CONTENTS
   1. Settings        - boom/bust thresholds
   2. PlayerReport    - every metric calculated for one player
   3. Math helpers    - percentile() and slope()
   4. analyze()       - main entry point: game logs in, reports out
   5. Value over replacement (VOR) and positional rank
   6. find_player()   - look a player up by full or partial name

 PIPELINE
   game logs -> score each game -> group by player -> per-player stats
             -> compare against position (boom/bust, VOR, rank) -> reports
=============================================================================
"""

import statistics
from collections import defaultdict
from dataclasses import dataclass

from .data import GameLog
from .scoring import ScoringSystem


# ---------------------------------------------------------------------------
# SECTION 1: SETTINGS
# Thresholds are relative to the average game at the player's position, so
# they work for any sport without per-position tuning.
# ---------------------------------------------------------------------------
BOOM_MULTIPLIER = 1.5  # game >= 1.5x the position's average game is a boom
BUST_MULTIPLIER = 0.5  # game <= 0.5x the position's average game is a bust


# ---------------------------------------------------------------------------
# SECTION 2: PLAYER REPORT
# The result for one player. Every number shown by the CLI comes from here.
# ---------------------------------------------------------------------------
@dataclass
class PlayerReport:
    # --- 2a. Identity --------------------------------------------------
    player: str
    position: str
    team: str
    weekly: list[tuple[int, float]]  # (week, fantasy points), sorted by week

    # --- 2b. Volume ----------------------------------------------------
    total: float
    ppg: float  # points per game
    median: float

    # --- 2c. Volatility / range ---------------------------------------
    stdev: float
    floor: float  # 25th percentile game
    ceiling: float  # 90th percentile game
    boom_rate: float
    bust_rate: float

    # --- 2d. Form / trend ---------------------------------------------
    recent_ppg: float
    form_delta: float  # recent_ppg - ppg
    trend_slope: float  # points per week, least-squares fit

    # --- 2e. League context (filled in by section 5) ------------------
    vor: float = 0.0  # ppg above replacement level at the position
    pos_rank: int = 0

    # --- 2f. Derived values -------------------------------------------
    @property
    def games(self) -> int:
        return len(self.weekly)

    @property
    def consistency(self) -> float:
        """Coefficient of variation (stdev / mean). Lower is steadier."""
        return self.stdev / self.ppg if self.ppg > 0 else float("inf")


# ---------------------------------------------------------------------------
# SECTION 3: MATH HELPERS
# ---------------------------------------------------------------------------
def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile, pct in [0, 100]."""
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * pct / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def slope(xs: list[float], ys: list[float]) -> float:
    """Least-squares slope of ys against xs (how fast scores rise or fall per week)."""
    if len(xs) < 2:
        return 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom if denom else 0.0


# ---------------------------------------------------------------------------
# SECTION 4: MAIN ANALYSIS
# ---------------------------------------------------------------------------
def analyze(
    logs: list[GameLog],
    scoring: ScoringSystem,
    recent_games: int = 3,
    teams: int | None = None,
    starters: dict[str, int] | None = None,
) -> list[PlayerReport]:
    """Build a report for every player, with VOR and positional rank filled in."""
    # --- 4a. League shape: command-line overrides beat preset defaults ---
    teams = teams if teams is not None else scoring.teams
    starters = starters if starters is not None else scoring.starters

    # --- 4b. Group game logs by player --------------------------------
    by_player: dict[str, list[GameLog]] = defaultdict(list)
    for log in logs:
        by_player[log.player].append(log)

    # --- 4c. Score every game; collect each position's average game ---
    pos_games: dict[str, list[float]] = defaultdict(list)
    scored: dict[str, list[tuple[int, float]]] = {}
    for name, games in by_player.items():
        weekly = sorted((g.week, scoring.score(g.stats)) for g in games)
        scored[name] = weekly
        pos_games[games[0].position].extend(p for _, p in weekly)
    pos_mean = {pos: statistics.fmean(pts) for pos, pts in pos_games.items()}

    # --- 4d. Calculate each player's metrics --------------------------
    reports = []
    for name, weekly in scored.items():
        first = by_player[name][0]
        pts = [p for _, p in weekly]
        ppg = statistics.fmean(pts)
        recent = statistics.fmean(pts[-recent_games:])
        avg = pos_mean[first.position]
        reports.append(
            PlayerReport(
                player=name,
                position=first.position,
                team=by_player[name][-1].team,  # latest team, in case of a trade
                weekly=weekly,
                total=round(sum(pts), 2),
                ppg=ppg,
                median=statistics.median(pts),
                stdev=statistics.pstdev(pts),
                floor=percentile(pts, 25),
                ceiling=percentile(pts, 90),
                boom_rate=sum(p >= avg * BOOM_MULTIPLIER for p in pts) / len(pts),
                bust_rate=sum(p <= avg * BUST_MULTIPLIER for p in pts) / len(pts),
                recent_ppg=recent,
                form_delta=recent - ppg,
                trend_slope=slope([w for w, _ in weekly], pts),
            )
        )

    # --- 4e. Add league context (VOR and rank) ------------------------
    _apply_vor(reports, teams, starters)
    return reports


# ---------------------------------------------------------------------------
# SECTION 5: VALUE OVER REPLACEMENT (VOR) AND POSITIONAL RANK
# Example: 12 teams x 2 RB starters = 24 startable RBs. The 25th-best RB is
# "replacement level" (roughly what's on waivers). VOR = ppg - that RB's ppg.
# ---------------------------------------------------------------------------
def _apply_vor(reports: list[PlayerReport], teams: int, starters: dict[str, int]) -> None:
    """VOR = ppg minus the ppg of the first player outside the startable pool.

    Positions not listed in `starters` get a replacement level of 0.
    """
    by_pos: dict[str, list[PlayerReport]] = defaultdict(list)
    for r in reports:
        by_pos[r.position].append(r)
    for pos, group in by_pos.items():
        group.sort(key=lambda r: r.ppg, reverse=True)
        pool = teams * starters.get(pos, 0)
        replacement = group[min(pool, len(group) - 1)].ppg if pool else 0.0
        for i, r in enumerate(group, start=1):
            r.pos_rank = i
            r.vor = r.ppg - replacement


# ---------------------------------------------------------------------------
# SECTION 6: PLAYER LOOKUP
# ---------------------------------------------------------------------------
def find_player(reports: list[PlayerReport], query: str) -> PlayerReport:
    """Exact (case-insensitive) match first, then a unique substring match."""
    q = query.lower()
    exact = [r for r in reports if r.player.lower() == q]
    if exact:
        return exact[0]
    partial = [r for r in reports if q in r.player.lower()]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise LookupError(f"No player matching '{query}'")
    raise LookupError(f"'{query}' is ambiguous: {', '.join(sorted(r.player for r in partial))}")
