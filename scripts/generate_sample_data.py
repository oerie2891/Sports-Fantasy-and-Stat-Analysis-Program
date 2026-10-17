"""
=============================================================================
 SAMPLE DATA GENERATOR  (scripts/generate_sample_data.py)
=============================================================================
 PURPOSE
   Rebuilds data/sample_nfl_2026.csv: 17 made-up NFL players x 9 weeks of
   random-but-realistic stats. The data is synthetic, for demos and tests.

   Run from the repository root:  python scripts/generate_sample_data.py

 CONTENTS
   1. Settings       - random seed, weeks, output path
   2. Player list    - each player's average and spread for every stat
   3. Generator      - draws each week's stats and writes the CSV
=============================================================================
"""

import csv
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# SECTION 1: SETTINGS
# A fixed seed means the same CSV is produced every run.
# ---------------------------------------------------------------------------
SEED = 7
WEEKS = range(1, 10)
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_nfl_2026.csv"
COLUMNS = ["pass_yds", "pass_td", "int", "rush_yds", "rush_td", "rec", "rec_yds", "rec_td", "fumbles_lost"]

# ---------------------------------------------------------------------------
# SECTION 2: PLAYER LIST
# (name, position, team, {stat: (average per game, standard deviation)})
# ---------------------------------------------------------------------------
PLAYERS = [
    # --- Quarterbacks ---
    ("Marcus Hale", "QB", "BUF", dict(pass_yds=(270, 50), pass_td=(2.0, 1), int=(0.7, .7), rush_yds=(30, 15), rush_td=(.3, .5))),
    ("Devon Price", "QB", "KC", dict(pass_yds=(250, 70), pass_td=(1.8, 1.2), int=(.8, .8), rush_yds=(12, 8), rush_td=(.1, .3))),
    ("Tyler Brooks", "QB", "DET", dict(pass_yds=(230, 40), pass_td=(1.4, .8), int=(.6, .6), rush_yds=(8, 6), rush_td=(.05, .2))),
    # --- Running backs ---
    ("Jalen Ortiz", "RB", "SF", dict(rush_yds=(95, 25), rush_td=(.9, .7), rec=(4, 1.5), rec_yds=(35, 15), fumbles_lost=(.1, .3))),
    ("Andre Simms", "RB", "ATL", dict(rush_yds=(80, 45), rush_td=(.7, .9), rec=(2, 1.5), rec_yds=(15, 12), fumbles_lost=(.1, .3))),
    ("Kenny Walsh", "RB", "MIA", dict(rush_yds=(60, 20), rush_td=(.4, .5), rec=(3.5, 1.5), rec_yds=(28, 12))),
    ("Chris Navarro", "RB", "DAL", dict(rush_yds=(45, 20), rush_td=(.3, .5), rec=(1.5, 1), rec_yds=(10, 8))),
    ("Leon Grant", "RB", "NYJ", dict(rush_yds=(30, 15), rush_td=(.2, .4), rec=(2, 1), rec_yds=(14, 8))),
    # --- Wide receivers ---
    ("Isaiah Cole", "WR", "MIN", dict(rec=(7, 2), rec_yds=(95, 30), rec_td=(.7, .7))),
    ("Ricky Dunn", "WR", "CIN", dict(rec=(5, 2.5), rec_yds=(75, 45), rec_td=(.6, .8))),
    ("Sam Whitfield", "WR", "PHI", dict(rec=(6, 1.5), rec_yds=(70, 20), rec_td=(.4, .5))),
    ("Omar Bishop", "WR", "LAR", dict(rec=(4, 2), rec_yds=(55, 30), rec_td=(.3, .5))),
    ("Nate Kessler", "WR", "SEA", dict(rec=(3, 1.5), rec_yds=(40, 20), rec_td=(.2, .4))),
    ("Jordan Fry", "WR", "HOU", dict(rec=(3, 2), rec_yds=(35, 25), rec_td=(.2, .4))),
    # --- Tight ends ---
    ("Grant Holloway", "TE", "KC", dict(rec=(5.5, 1.5), rec_yds=(60, 20), rec_td=(.5, .6))),
    ("Mike Abara", "TE", "BAL", dict(rec=(4, 1.5), rec_yds=(45, 20), rec_td=(.4, .5))),
    ("Luke Tanner", "TE", "GB", dict(rec=(2.5, 1.5), rec_yds=(25, 15), rec_td=(.2, .4))),
]


# ---------------------------------------------------------------------------
# SECTION 3: GENERATOR
# ---------------------------------------------------------------------------
def drift(name: str, week: int) -> float:
    """Built-in storylines: Kenny Walsh improves over the season, Ricky Dunn fades."""
    if name == "Kenny Walsh":
        return 1 + 0.06 * (week - 5)
    if name == "Ricky Dunn":
        return 1 - 0.05 * (week - 5)
    return 1.0


def main() -> None:
    random.seed(SEED)
    with open(OUTPUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player", "position", "team", "week", *COLUMNS])
        for name, pos, team, dist in PLAYERS:
            for wk in WEEKS:
                if name == "Andre Simms" and wk == 5:
                    continue  # simulates a missed game
                row = []
                for c in COLUMNS:
                    if c in dist:
                        mean, sd = dist[c]
                        row.append(round(max(0, random.gauss(mean * drift(name, wk), sd))))
                    else:
                        row.append("")  # stat not relevant to this position
                w.writerow([name, pos, team, wk, *row])
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
