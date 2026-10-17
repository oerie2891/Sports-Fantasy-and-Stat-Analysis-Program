# Sports-Fantasy-and-Stat-Analysis-Program
Helps with fantasy matchups, analysing players' and teams' performances both stat-wise and fantasy score-wise, and analyses potential trade proposals and waivers/free agency, as well as advises starting lineups each matchup 

## Player performance analyzer

A dependency-free Python (3.10+) tool that turns per-game stat logs into fantasy performance reports.

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

`data/sample_nfl_2026.csv` is **synthetic** data with made-up players, for demoing only. Use your own
export for real decisions.

### Input format

A CSV with one row per player per game: `player`, `position`, `week`, an optional `team`, and any stat
columns your scoring preset uses. Blank cells count as 0.

| Preset | Stat columns |
|---|---|
| `nfl-standard`, `nfl-half-ppr` (default), `nfl-ppr` | `pass_yds pass_td int rush_yds rush_td rec rec_yds rec_td fumbles_lost two_pt` |
| `nba-points` | `pts reb ast stl blk tov fg3m` |

Set your league shape with `--teams 10 --starters QB=1,RB=2,WR=3,TE=1`. It drives the replacement level.

### Metrics

| Metric | Meaning |
|---|---|
| PPG / Median | Average and median fantasy points per game |
| VOR | PPG minus the PPG of the best player who wouldn't start in your league (teams x starters) |
| Floor / Ceiling | 25th / 90th percentile game |
| CV | Standard deviation / PPG. Lower means more consistent |
| Boom / Bust | Share of games at least 1.5x / at most 0.5x the position's average game |
| Form | Last `--recent` games' PPG minus season PPG |
| Trend | Least-squares slope of points per week |

### Tests

```bash
python -m unittest
```
