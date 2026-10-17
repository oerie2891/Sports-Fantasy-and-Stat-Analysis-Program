"""Turn game logs into per-player fantasy performance reports."""

import statistics
from collections import defaultdict
from dataclasses import dataclass

from .data import GameLog
from .scoring import ScoringSystem

BOOM_MULTIPLIER = 1.5  # game >= 1.5x the position's average game is a boom
BUST_MULTIPLIER = 0.5  # game <= 0.5x the position's average game is a bust


@dataclass
class PlayerReport:
    player: str
    position: str
    team: str
    weekly: list[tuple[int, float]]  # (week, fantasy points), sorted by week
    total: float
    ppg: float
    median: float
    stdev: float
    floor: float  # 25th percentile game
    ceiling: float  # 90th percentile game
    boom_rate: float
    bust_rate: float
    recent_ppg: float
    form_delta: float  # recent_ppg - ppg
    trend_slope: float  # points per week, least-squares fit
    vor: float = 0.0  # ppg above replacement level at the position
    pos_rank: int = 0

    @property
    def games(self) -> int:
        return len(self.weekly)

    @property
    def consistency(self) -> float:
        """Coefficient of variation (stdev / mean). Lower is steadier."""
        return self.stdev / self.ppg if self.ppg > 0 else float("inf")


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
    if len(xs) < 2:
        return 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom if denom else 0.0


def analyze(
    logs: list[GameLog],
    scoring: ScoringSystem,
    recent_games: int = 3,
    teams: int | None = None,
    starters: dict[str, int] | None = None,
) -> list[PlayerReport]:
    """Build a report for every player, with VOR and positional rank filled in."""
    teams = teams if teams is not None else scoring.teams
    starters = starters if starters is not None else scoring.starters

    by_player: dict[str, list[GameLog]] = defaultdict(list)
    for log in logs:
        by_player[log.player].append(log)

    pos_games: dict[str, list[float]] = defaultdict(list)
    scored: dict[str, list[tuple[int, float]]] = {}
    for name, games in by_player.items():
        weekly = sorted((g.week, scoring.score(g.stats)) for g in games)
        scored[name] = weekly
        pos_games[games[0].position].extend(p for _, p in weekly)
    pos_mean = {pos: statistics.fmean(pts) for pos, pts in pos_games.items()}

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
                team=by_player[name][-1].team,
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

    _apply_vor(reports, teams, starters)
    return reports


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
