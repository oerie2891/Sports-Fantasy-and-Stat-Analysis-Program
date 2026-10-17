"""Command-line interface: python -m fantasy_analyzer <command> ..."""

import argparse
import sys

from .analysis import PlayerReport, analyze, find_player
from .data import load_game_logs
from .scoring import PRESETS, get_scoring


def parse_starters(text: str) -> dict[str, int]:
    out = {}
    for part in text.split(","):
        pos, _, n = part.partition("=")
        if not n:
            raise argparse.ArgumentTypeError(f"bad starters entry '{part}', expected POS=N")
        out[pos.strip().upper()] = int(n)
    return out


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _signed(x: float) -> str:
    return f"{x:+.1f}"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) if i < 2 else h.rjust(w) for i, (h, w) in enumerate(zip(headers, widths))))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(c.ljust(w) if i < 2 else c.rjust(w) for i, (c, w) in enumerate(zip(r, widths))))


def cmd_rank(reports: list[PlayerReport], args: argparse.Namespace) -> None:
    pool = [r for r in reports if r.games >= args.min_games]
    if args.position:
        pool = [r for r in pool if r.position == args.position.upper()]
    key = {
        "vor": lambda r: r.vor,
        "ppg": lambda r: r.ppg,
        "total": lambda r: r.total,
        "ceiling": lambda r: r.ceiling,
        "floor": lambda r: r.floor,
        "form": lambda r: r.form_delta,
        "consistency": lambda r: -r.consistency,
    }[args.sort]
    pool.sort(key=key, reverse=True)
    rows = [
        [
            r.player,
            f"{r.position}{r.pos_rank}",
            str(r.games),
            f"{r.ppg:.1f}",
            _signed(r.vor),
            f"{r.floor:.1f}",
            f"{r.ceiling:.1f}",
            f"{r.consistency:.2f}",
            _pct(r.boom_rate),
            _pct(r.bust_rate),
            _signed(r.form_delta),
        ]
        for r in pool[: args.limit]
    ]
    print_table(["Player", "Pos", "GP", "PPG", "VOR", "Floor", "Ceil", "CV", "Boom", "Bust", "Form"], rows)


def describe(r: PlayerReport) -> list[str]:
    """Plain-language takeaways derived from the numbers."""
    notes = []
    if r.vor > 0:
        notes.append(f"Startable: {r.vor:.1f} PPG above replacement-level {r.position}.")
    else:
        notes.append(f"Below replacement level at {r.position} ({r.vor:.1f} PPG) — streamer/bench territory.")
    if r.consistency < 0.35:
        notes.append("Steady producer: low week-to-week variance, safe floor.")
    elif r.consistency > 0.6:
        notes.append("Volatile: big swings week to week — better in best-ball or when you need upside.")
    if r.form_delta >= 3:
        notes.append(f"Trending up: last games averaging {r.recent_ppg:.1f} vs {r.ppg:.1f} season.")
    elif r.form_delta <= -3:
        notes.append(f"Cooling off: last games averaging {r.recent_ppg:.1f} vs {r.ppg:.1f} season.")
    if r.games < 4:
        notes.append(f"Small sample ({r.games} games) — treat every number above with caution.")
    return notes


def cmd_player(reports: list[PlayerReport], args: argparse.Namespace) -> None:
    r = find_player(reports, args.name)
    print(f"{r.player}  ({r.position}{r.pos_rank}{', ' + r.team if r.team else ''})")
    print(f"  Games {r.games}   Total {r.total:.1f}   PPG {r.ppg:.1f}   Median {r.median:.1f}   VOR {_signed(r.vor)}")
    print(f"  Floor {r.floor:.1f}   Ceiling {r.ceiling:.1f}   StDev {r.stdev:.1f}   CV {r.consistency:.2f}")
    print(f"  Boom {_pct(r.boom_rate)}   Bust {_pct(r.bust_rate)}")
    print(f"  Recent PPG {r.recent_ppg:.1f} ({_signed(r.form_delta)})   Trend {_signed(r.trend_slope)} pts/week")
    print("\n  Week-by-week:")
    peak = max((p for _, p in r.weekly), default=0) or 1
    for week, pts in r.weekly:
        print(f"    Wk {week:>2}  {pts:>6.1f}  {'#' * round(pts / peak * 30)}")
    print("\n  Takeaways:")
    for note in describe(r):
        print(f"    - {note}")


def cmd_compare(reports: list[PlayerReport], args: argparse.Namespace) -> None:
    players = [find_player(reports, n) for n in args.names]
    metrics = [
        ("Position", lambda r: f"{r.position}{r.pos_rank}", None),
        ("Games", lambda r: str(r.games), None),
        ("PPG", lambda r: f"{r.ppg:.1f}", lambda r: r.ppg),
        ("VOR", lambda r: _signed(r.vor), lambda r: r.vor),
        ("Floor", lambda r: f"{r.floor:.1f}", lambda r: r.floor),
        ("Ceiling", lambda r: f"{r.ceiling:.1f}", lambda r: r.ceiling),
        ("CV (lower=steadier)", lambda r: f"{r.consistency:.2f}", lambda r: -r.consistency),
        ("Boom rate", lambda r: _pct(r.boom_rate), lambda r: r.boom_rate),
        ("Bust rate", lambda r: _pct(r.bust_rate), lambda r: -r.bust_rate),
        ("Recent PPG", lambda r: f"{r.recent_ppg:.1f}", lambda r: r.recent_ppg),
    ]
    rows = []
    for label, fmt, better in metrics:
        cells = [fmt(r) for r in players]
        if better:
            values = [round(better(r), 2) for r in players]
            if len(set(values)) > 1:  # no star when everyone ties
                cells = [c + " *" if v == max(values) else c for c, v in zip(cells, values)]
        rows.append([label, *cells])
    print_table(["Metric", *[r.player for r in players]], rows)
    print("\n* = better on that metric")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fantasy_analyzer", description="Analyse player performance in fantasy sports.")
    p.add_argument("--data", required=True, help="CSV of per-game stats (player, position, week, stat columns...)")
    p.add_argument("--scoring", default="nfl-half-ppr", choices=sorted(PRESETS), help="scoring preset")
    p.add_argument("--teams", type=int, help="league size (default: preset's)")
    p.add_argument("--starters", type=parse_starters, help="starters per team, e.g. QB=1,RB=2,WR=3,TE=1")
    p.add_argument("--recent", type=int, default=3, help="games counted as 'recent form' (default 3)")
    sub = p.add_subparsers(dest="command", required=True)

    rank = sub.add_parser("rank", help="rank players")
    rank.add_argument("-p", "--position")
    rank.add_argument(
        "-s", "--sort", default="vor", choices=["vor", "ppg", "total", "ceiling", "floor", "form", "consistency"]
    )
    rank.add_argument("-n", "--limit", type=int, default=25)
    rank.add_argument("--min-games", type=int, default=1)
    rank.set_defaults(func=cmd_rank)

    player = sub.add_parser("player", help="detailed report for one player")
    player.add_argument("name")
    player.set_defaults(func=cmd_player)

    compare = sub.add_parser("compare", help="side-by-side comparison of two or more players")
    compare.add_argument("names", nargs="+")
    compare.set_defaults(func=cmd_compare)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        logs = load_game_logs(args.data)
        if not logs:
            raise ValueError(f"{args.data}: no rows")
        reports = analyze(logs, get_scoring(args.scoring), args.recent, args.teams, args.starters)
        args.func(reports, args)
    except (OSError, ValueError, LookupError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
