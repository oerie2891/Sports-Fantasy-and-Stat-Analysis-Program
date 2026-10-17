# Sports-Fantasy-and-Stat-Analysis-Program

Helps with fantasy matchups, analysing players' and teams' performances both stat-wise and fantasy score-wise, and analyses potential trade proposals and waivers/free agency, as well as advises starting lineups each matchup.

## Status

| Feature | State |
|---|---|
| Player performance analysis (rank, player report, compare) | **Built** |
| Live data feed (Sleeper / ESPN / Yahoo / nflverse) | Not started. You supply a CSV |
| Matchup / opponent-strength adjustment | Not started |
| Trade analyser | Not started |
| Waiver / free-agent recommendations | Not started |
| Start/sit lineup advice | Not started |

## Quick start

Requires Python 3.10 or newer. No extra packages needed.

```bash
# Rank every player by value over replacement (VOR)
python -m fantasy_analyzer --data data/sample_nfl_2026.csv --teams 2 rank

# Only WRs, sorted by ceiling, PPR scoring
python -m fantasy_analyzer --data data/sample_nfl_2026.csv --scoring nfl-ppr rank -p WR -s ceiling

# Deep dive on one player (partial names work)
python -m fantasy_analyzer --data data/sample_nfl_2026.csv player walsh

# Side-by-side comparison
python -m fantasy_analyzer --data data/sample_nfl_2026.csv compare "Isaiah Cole" "Ricky Dunn"
```

> `data/sample_nfl_2026.csv` is **synthetic** data with made-up players, for demoing only. Use your own
> export for real decisions.

## Command reference

Global options go **before** the command name.

| Option | Default | Meaning |
|---|---|---|
| `--data FILE` | required | CSV of per-game stats |
| `--scoring NAME` | `nfl-half-ppr` | `nfl-standard`, `nfl-half-ppr`, `nfl-ppr`, `nba-points` |
| `--teams N` | preset (12) | League size |
| `--starters POS=N,...` | preset | Starters per team, e.g. `QB=1,RB=2,WR=3,TE=1` |
| `--recent N` | 3 | How many latest games count as "recent form" |

| Command | Options |
|---|---|
| `rank` | `-p/--position`, `-s/--sort` (`vor` `ppg` `total` `ceiling` `floor` `form` `consistency`), `-n/--limit`, `--min-games` |
| `player NAME` | none |
| `compare NAME NAME [...]` | none |

## Metrics

| Metric | Meaning |
|---|---|
| PPG / Median | Average and median fantasy points per game |
| VOR | PPG minus the PPG of the best player who wouldn't start in your league (teams x starters) |
| Floor / Ceiling | 25th / 90th percentile game |
| CV | Standard deviation / PPG. Lower means more consistent |
| Boom / Bust | Share of games at least 1.5x / at most 0.5x the position's average game |
| Form | Last `--recent` games' PPG minus season PPG |
| Trend | Least-squares slope of points per week |

## Project layout

```
.
├── README.md                    <- you are here: overview and usage
├── fantasy_analyzer/            <- the program itself
│   ├── README.md                <- code guide: what every file and section does
│   ├── __init__.py              <- library interface (import fantasy_analyzer)
│   ├── __main__.py              <- launcher for `python -m fantasy_analyzer`
│   ├── cli.py                   <- commands, options, printed output
│   ├── analysis.py              <- the maths: PPG, VOR, floor/ceiling, boom/bust...
│   ├── data.py                  <- reads and validates the CSV
│   └── scoring.py               <- scoring formats (stats -> fantasy points)
├── data/
│   ├── README.md                <- CSV format and how to bring your own data
│   └── sample_nfl_2026.csv      <- synthetic demo data
├── scripts/
│   ├── README.md
│   └── generate_sample_data.py  <- rebuilds the sample CSV
└── tests/
    ├── README.md                <- what is tested and how to run it
    └── test_analysis.py
```

Every Python file opens with a header box (purpose and contents), and its code is split into numbered
`SECTION` blocks that match the contents list. Start with [`fantasy_analyzer/README.md`](fantasy_analyzer/README.md).

## Running the tests

```bash
python -m unittest -v
```
