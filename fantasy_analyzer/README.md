# Code guide: `fantasy_analyzer/`

This folder is the whole program. This guide explains what each file does, how data moves between
them, and which numbered `SECTION` in each file does what. The section numbers here match the
`# SECTION n:` banners in the code.

## How the files fit together

```
 you type a command
        │
        ▼
 __main__.py ──► cli.py  (SECTION 6: read options, SECTION 7: run)
                   │
                   ├──► data.py      reads CSV  ──► list of GameLog (one per player per game)
                   │
                   ├──► scoring.py   chooses rules for turning stats into points
                   │
                   ├──► analysis.py  GameLogs + rules ──► list of PlayerReport (one per player)
                   │
                   └──► cli.py       (SECTIONS 3-5) prints rank / player / compare output
```

Dependencies only point one way: `cli` uses `analysis`, `data` and `scoring`. `analysis` uses
`data` and `scoring`. `data` and `scoring` use nothing else in the project. So you can change how
output looks without touching the maths, and change the maths without touching the CSV reader.

---

## `scoring.py`: stats → fantasy points

| Section | What it does |
|---|---|
| 1. ScoringSystem | One scoring format: points per stat, plus default league size and starters. `score()` turns one game's stats into points |
| 2. Presets | `_NFL_BASE` holds shared NFL rules. `PRESETS` lists every format (`nfl-standard`, `nfl-half-ppr`, `nfl-ppr`, `nba-points`) |
| 3. get_scoring() | Looks up a preset by name and raises a clear error for unknown names |

**Change this file when** your league scores differently, for example 6-point passing TDs or bonuses.
Add a new entry to `PRESETS` and it appears automatically as a `--scoring` option.

## `data.py`: reading the CSV

| Section | What it does |
|---|---|
| 1. Column rules | `REQUIRED` columns must exist. `META` columns are labels. Everything else is a stat |
| 2. GameLog | One player's stats for one week |
| 3. load_game_logs() | 3a checks the header. 3b converts each row and reports the line number of a bad row |

**Change this file when** you add a new data source. Write a function that returns `list[GameLog]`
and the rest of the program works unchanged.

## `analysis.py`: the maths

| Section | What it does |
|---|---|
| 1. Settings | Boom (≥1.5x) and bust (≤0.5x) thresholds, relative to the position's average game |
| 2. PlayerReport | Every metric for one player, grouped: 2a identity, 2b volume, 2c volatility, 2d form, 2e league context, 2f derived values (`games`, `consistency`) |
| 3. Math helpers | `percentile()` for floor/ceiling, `slope()` for the trend line |
| 4. analyze() | Main function. 4a league shape, 4b group by player, 4c score each game and get position averages, 4d calculate metrics, 4e add VOR |
| 5. _apply_vor() | Ranks players within each position and calculates value over replacement |
| 6. find_player() | Finds a player by exact name first, then by a unique partial match |

**VOR in one example.** In a 12-team league with 2 starting RBs, 24 RBs start each week. The 25th
best RB is "replacement level", roughly what's on waivers. If that RB averages 9 PPG and your RB
averages 15, your RB's VOR is +6.

**Change this file when** you want a new metric. Add a field to `PlayerReport` (section 2),
calculate it in section 4d, then display it in `cli.py`.

## `cli.py`: commands and output

| Section | What it does |
|---|---|
| 1. Input parsing | `parse_starters()` turns `QB=1,RB=2` into a dictionary |
| 2. Output formatting | `_pct`, `_signed`, and `print_table()` for aligned columns |
| 3. `rank` | 3a filter, 3b sort by chosen metric, 3c print leaderboard |
| 4. `player` | 4a `describe()` writes plain-English takeaways, 4b prints summary, weekly bar chart and takeaways |
| 5. `compare` | 5a metric list (label, display, which direction is better), 5b builds rows and stars the leader |
| 6. Arguments | 6a global options, 6b–6d each command's options |
| 7. main() | Loads data, runs analysis, calls the command, and turns known errors into a one-line message |

**Change this file when** you want a new command (add a `cmd_*` function and register it in
section 6) or different output.

## `__init__.py` and `__main__.py`

- `__init__.py` defines what `import fantasy_analyzer` exposes, so you can use the analysis from
  your own scripts or a notebook:
  ```python
  from fantasy_analyzer import load_game_logs, get_scoring, analyze
  reports = analyze(load_game_logs("my.csv"), get_scoring("nfl-ppr"))
  best = max(reports, key=lambda r: r.vor)
  ```
- `__main__.py` is what runs for `python -m fantasy_analyzer`. It calls `cli.main()`.
