import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

class ProjectSmokeTests(unittest.TestCase):
    def test_input_data_exists_and_has_expected_columns(self):
        from src.config import ASSETS, BENCHMARK, DATA_FILE
        self.assertTrue(DATA_FILE.exists())
        df = pd.read_csv(DATA_FILE)
        self.assertTrue(set(["Date", *ASSETS, BENCHMARK]).issubset(df.columns))

    def test_initial_weights_are_valid(self):
        from src.config import ASSETS, INITIAL_WEIGHTS
        self.assertEqual(len(ASSETS), len(INITIAL_WEIGHTS))
        self.assertAlmostEqual(float(INITIAL_WEIGHTS.sum()), 1.0, places=10)
        self.assertTrue((INITIAL_WEIGHTS >= 0).all())

    def test_core_output_contract_exists_after_a_project_run(self):
        out = ROOT / "outputs"
        required = [
            "portfolio_kpis.csv",
            "asset_statistics.csv",
            "risk_contribution.csv",
            "optimization_summary.csv",
            "qa_checks.csv",
        ]
        missing = [name for name in required if not (out / name).exists()]
        self.assertFalse(missing, f"Missing generated outputs: {missing}")

if __name__ == "__main__":
    unittest.main()
