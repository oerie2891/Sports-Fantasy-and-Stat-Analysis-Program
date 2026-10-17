# Tests

Automated checks that the program still gives correct answers after you change it. Run them after
every edit.

```bash
python -m unittest -v          # from the repository root
```

All tests should print `ok`. A `FAIL` or `ERROR` names the test and shows the expected and actual
values.

## What's covered (`test_analysis.py`)

| Section | Class | Checks |
|---|---|---|
| 0 | fixtures | Sample file path, a one-stat scoring system, and a helper that builds game logs |
| 1 | `ScoringTests` | One stat line scores 12 / 14.5 / 17 in standard / half / full PPR, and unknown presets are rejected |
| 2 | `StatHelperTests` | Percentile and slope against hand-calculated values |
| 3 | `AnalyzeTests` | Three made-up players (Star, Mid, Scrub): totals, PPG, recent form, VOR, rank, consistency, boom/bust, name lookup |
| 4 | `DataAndCliTests` | Loading the sample CSV, a missing-column error, all three commands, and the unknown-player error |

## Adding a test

Add a method whose name starts with `test_` to the class that matches the area you changed. Work out
the expected answer by hand first, then assert it. A test that only checks "something printed"
catches crashes, but it won't catch wrong numbers.
