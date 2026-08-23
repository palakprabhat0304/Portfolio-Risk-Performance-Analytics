"""Central configuration for the portfolio analytics project.

Edit this file to change the portfolio, benchmark, risk assumptions, or
simulation settings without hunting through the analysis code.
"""
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "market_prices_demo.csv"
OUTPUT_DIR = BASE_DIR / "outputs"

ASSETS = [
    "RELIANCE", "HDFCBANK", "TCS", "INFY",
    "ITC", "LT", "SUNPHARMA", "BHARTIARTL",
]
BENCHMARK = "NIFTY50"

# Current / baseline portfolio weights. Keep the order identical to ASSETS.
INITIAL_WEIGHTS = np.array([0.15, 0.15, 0.15, 0.10, 0.10, 0.15, 0.10, 0.10], dtype=float)

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.06

MONTE_CARLO_PATHS = 10_000
MONTE_CARLO_DAYS = 252
MONTE_CARLO_SEED = 123

PRACTICAL_MAX_WEIGHT = 0.30
VAR_CONFIDENCE = 0.95

# Optional reporting labels.
PORTFOLIO_NAME = "Current Portfolio"
BENCHMARK_LABEL = "NIFTY 50"
