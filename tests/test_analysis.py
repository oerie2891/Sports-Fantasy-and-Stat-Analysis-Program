import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from fantasy_analyzer import GameLog, ScoringSystem, analyze, find_player, get_scoring, load_game_logs
from fantasy_analyzer.analysis import percentile, slope
from fantasy_analyzer.cli import main

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_nfl_2026.csv"
SIMPLE = ScoringSystem("test", {"pts": 1.0}, {"X": 1}, teams=1)


def logs(player, position, scores):
    return [GameLog(player, position, "", week, {"pts": s}) for week, s in enumerate(scores, start=1)]


class ScoringTests(unittest.TestCase):
    def test_ppr_vs_standard(self):
        line = {"rec": 5, "rec_yds": 60, "rec_td": 1}
        self.assertEqual(get_scoring("nfl-standard").score(line), 12.0)
        self.assertEqual(get_scoring("nfl-half-ppr").score(line), 14.5)
        self.assertEqual(get_scoring("nfl-ppr").score(line), 17.0)

    def test_unknown_preset(self):
        with self.assertRaises(ValueError):
            get_scoring("cricket")


class StatHelperTests(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 50), 3)
        self.assertEqual(percentile([10, 20], 25), 12.5)
        self.assertEqual(percentile([], 50), 0.0)

    def test_slope(self):
        self.assertAlmostEqual(slope([1, 2, 3], [2, 4, 6]), 2.0)
        self.assertEqual(slope([1], [5]), 0.0)


class AnalyzeTests(unittest.TestCase):
    def setUp(self):
        data = logs("Star", "X", [20, 22, 18, 30]) + logs("Mid", "X", [10, 10, 10, 10]) + logs("Scrub", "X", [4, 2, 6, 0])
        self.reports = {r.player: r for r in analyze(data, SIMPLE, recent_games=2)}

    def test_basic_metrics(self):
        star = self.reports["Star"]
        self.assertEqual(star.games, 4)
        self.assertEqual(star.total, 90)
        self.assertEqual(star.ppg, 22.5)
        self.assertEqual(star.recent_ppg, 24)
        self.assertEqual(star.form_delta, 1.5)

    def test_vor_uses_first_player_outside_starting_pool(self):
        # 1 team x 1 starter -> replacement is the 2nd best player (Mid, 10 ppg)
        self.assertEqual(self.reports["Star"].vor, 12.5)
        self.assertEqual(self.reports["Mid"].vor, 0)
        self.assertEqual(self.reports["Star"].pos_rank, 1)

    def test_consistency(self):
        self.assertEqual(self.reports["Mid"].consistency, 0)
        self.assertGreater(self.reports["Scrub"].consistency, self.reports["Star"].consistency)

    def test_boom_bust_relative_to_position_average(self):
        # position average = (90 + 40 + 12) / 12 = 11.83; boom >= 17.75, bust <= 5.92
        self.assertEqual(self.reports["Star"].boom_rate, 1.0)
        self.assertEqual(self.reports["Scrub"].bust_rate, 0.75)

    def test_find_player(self):
        reports = list(self.reports.values())
        self.assertEqual(find_player(reports, "star").player, "Star")
        self.assertEqual(find_player(reports, "scr").player, "Scrub")
        with self.assertRaises(LookupError):
            find_player(reports, "nobody")


class DataAndCliTests(unittest.TestCase):
    def test_loads_sample(self):
        data = load_game_logs(SAMPLE)
        self.assertTrue(data)
        self.assertEqual(data[0].stats.get("rec"), 0.0)  # blank cell -> 0

    def test_missing_column(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("player,week\nA,1\n")
        with self.assertRaisesRegex(ValueError, "position"):
            load_game_logs(f.name)

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(["--data", str(SAMPLE), *args])
        return code, out.getvalue()

    def test_commands(self):
        for args in (["rank", "-p", "wr"], ["player", "Isaiah Cole"], ["compare", "Jalen Ortiz", "Andre Simms"]):
            code, out = self.run_cli(*args)
            self.assertEqual(code, 0, out)
            self.assertTrue(out.strip())

    def test_unknown_player_is_an_error(self):
        code, out = self.run_cli("player", "Nobody Atall")
        self.assertEqual(code, 1)
        self.assertIn("No player matching", out)


if __name__ == "__main__":
    unittest.main()
