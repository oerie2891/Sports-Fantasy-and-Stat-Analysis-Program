# Scripts

Helper scripts that aren't part of the program itself.

| Script | What it does | Run with |
|---|---|---|
| `generate_sample_data.py` | Rebuilds `data/sample_nfl_2026.csv` from a fixed random seed, so the output is identical every run | `python scripts/generate_sample_data.py` |

To change the sample players, edit the `PLAYERS` list (SECTION 2) in the script, re-run it, then run
the tests. Tests that use the sample file may need updating if a player's name changes.
