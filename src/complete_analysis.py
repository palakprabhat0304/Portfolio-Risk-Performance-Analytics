import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# -----------------------------
# Configuration
# -----------------------------
from config import (
    ASSETS, BENCHMARK, DATA_FILE, OUTPUT_DIR, INITIAL_WEIGHTS,
    TRADING_DAYS_PER_YEAR, RISK_FREE_RATE, MONTE_CARLO_PATHS,
    MONTE_CARLO_DAYS, MONTE_CARLO_SEED,
)

BASE = str(DATA_FILE.parent.parent)
DATA = str(DATA_FILE)
OUT = str(OUTPUT_DIR)
os.makedirs(OUT, exist_ok=True)
W0 = INITIAL_WEIGHTS.copy()
ANN = TRADING_DAYS_PER_YEAR
RF = RISK_FREE_RATE
MC_PATHS = MONTE_CARLO_PATHS
MC_DAYS = MONTE_CARLO_DAYS

# -----------------------------
# Data loading and validation
# -----------------------------
prices = pd.read_csv(DATA, parse_dates=["Date"])
required = ["Date", *ASSETS, BENCHMARK]
missing = [c for c in required if c not in prices.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")
if prices["Date"].duplicated().any():
    raise ValueError("Duplicate dates found in input data.")
prices = prices.sort_values("Date").set_index("Date")
prices[ASSETS + [BENCHMARK]] = prices[ASSETS + [BENCHMARK]].apply(pd.to_numeric, errors="coerce")
prices = prices.dropna(subset=ASSETS + [BENCHMARK])
if (prices[ASSETS + [BENCHMARK]] <= 0).any().any():
    raise ValueError("Prices must be positive.")
if len(ASSETS) != len(W0):
    raise ValueError("ASSETS and INITIAL_WEIGHTS must have the same length.")
if np.any(W0 < 0):
    raise ValueError("Portfolio weights cannot be negative.")
if not np.isclose(W0.sum(), 1):
    raise ValueError("Portfolio weights must sum to 100%.")

R = prices[ASSETS].pct_change().dropna()
B = prices[BENCHMARK].pct_change().dropna()
port = R @ W0
common = pd.concat([port.rename("Portfolio"), B.rename("Benchmark")], axis=1).dropna()
port, B = common["Portfolio"], common["Benchmark"]

# -----------------------------
# Metrics
# -----------------------------
def annual_return(r):
    return (1 + r).prod() ** (ANN / len(r)) - 1

def annual_vol(r):
    return r.std(ddof=1) * np.sqrt(ANN)

def sharpe(r):
    return (r.mean() * ANN - RF) / annual_vol(r)

def sortino(r):
    target_daily = RF / ANN
    downside = np.minimum(r - target_daily, 0)
    downside_dev = np.sqrt(np.mean(downside ** 2)) * np.sqrt(ANN)
    return (r.mean() * ANN - RF) / downside_dev if downside_dev else np.nan

def drawdown(r):
    wealth = (1 + r).cumprod()
    return wealth / wealth.cummax() - 1

def historical_var(r, confidence=0.95):
    return -np.quantile(r, 1 - confidence)

def expected_shortfall(r, confidence=0.95):
    q = np.quantile(r, 1 - confidence)
    tail = r[r <= q]
    return -tail.mean()

def beta_of(r, b):
    x = pd.concat([r, b], axis=1).dropna()
    return np.cov(x.iloc[:, 0], x.iloc[:, 1], ddof=1)[0, 1] / np.var(x.iloc[:, 1], ddof=1)

beta = beta_of(port, B)
alpha = port.mean() * ANN - RF - beta * (B.mean() * ANN - RF)
dd = drawdown(port)

metrics = pd.DataFrame({
    "Metric": [
        "Start Date", "End Date", "Trading Days", "Annual Return", "Annual Volatility",
        "Sharpe Ratio", "Sortino Ratio", "Maximum Drawdown", "Historical VaR 95% (Daily)",
        "Expected Shortfall 95% (Daily)", "Beta", "Jensen Alpha", "Benchmark Correlation"
    ],
    "Value": [
        prices.index.min().date(), prices.index.max().date(), len(R), annual_return(port),
        annual_vol(port), sharpe(port), sortino(port), dd.min(), historical_var(port),
        expected_shortfall(port), beta, alpha, port.corr(B)
    ]
})
metrics.to_csv(os.path.join(OUT, "portfolio_kpis.csv"), index=False)

# -----------------------------
# Asset-level analytics
# -----------------------------
asset_stats = pd.DataFrame({
    "Asset": ASSETS,
    "Weight": W0,
    "Annualized_Return": R.mean().values * ANN,
    "Annualized_Volatility": R.std().values * np.sqrt(ANN),
    "Sharpe_Ratio": [(x.mean() * ANN - RF) / (x.std() * np.sqrt(ANN)) for _, x in R.items()],
    "Beta_to_NIFTY50": [beta_of(R[a], B) for a in ASSETS],
})
asset_stats["Weight_Pct"] = asset_stats["Weight"] * 100
asset_stats.to_csv(os.path.join(OUT, "asset_statistics.csv"), index=False)

corr = R.corr()
corr.to_csv(os.path.join(OUT, "correlation_matrix.csv"))

# -----------------------------
# Risk contribution
# -----------------------------
covmat = R.cov() * ANN
sigma = np.sqrt(W0 @ covmat @ W0)
marginal = covmat @ W0 / sigma
rc = W0 * marginal
risk_contribution = pd.DataFrame({
    "Asset": ASSETS,
    "Weight": W0,
    "Risk_Contribution": rc,
    "Risk_Contribution_%": rc / sigma
})
risk_contribution.to_csv(os.path.join(OUT, "risk_contribution.csv"), index=False)

# -----------------------------
# Return attribution
# -----------------------------
attr = pd.DataFrame({
    "Asset": ASSETS,
    "Weight": W0,
    "Annualized_Return": R.mean().values * ANN
})
attr["Return_Contribution"] = attr["Weight"] * attr["Annualized_Return"]
attr["Return_Contribution_%"] = attr["Return_Contribution"] / attr["Return_Contribution"].sum()
attr.to_csv(os.path.join(OUT, "return_attribution.csv"), index=False)

# -----------------------------
# Optimization
# -----------------------------
mu = R.mean().values * ANN

def portfolio_vol(w):
    return np.sqrt(w @ covmat @ w)

def negative_sharpe(w):
    return -(w @ mu - RF) / portfolio_vol(w)

constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
bounds = [(0, 1)] * len(ASSETS)
x0 = np.repeat(1 / len(ASSETS), len(ASSETS))

minv = minimize(portfolio_vol, x0, method="SLSQP", bounds=bounds, constraints=constraints)
maxs = minimize(negative_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints)
if not minv.success or not maxs.success:
    raise RuntimeError("Portfolio optimization failed.")

optimized = pd.DataFrame({
    "Asset": ASSETS,
    "Current_Weight": W0,
    "Minimum_Volatility_Weight": minv.x,
    "Maximum_Sharpe_Weight": maxs.x
})
optimized.to_csv(os.path.join(OUT, "optimized_weights.csv"), index=False)

optimization_summary = pd.DataFrame({
    "Portfolio": ["Current", "Minimum Volatility", "Maximum Sharpe"],
    "Expected Annual Return": [W0 @ mu, minv.x @ mu, maxs.x @ mu],
    "Annual Volatility": [portfolio_vol(W0), portfolio_vol(minv.x), portfolio_vol(maxs.x)],
    "Sharpe Ratio": [(W0 @ mu - RF) / portfolio_vol(W0),
                     (minv.x @ mu - RF) / portfolio_vol(minv.x),
                     (maxs.x @ mu - RF) / portfolio_vol(maxs.x)]
})
optimization_summary.to_csv(os.path.join(OUT, "optimization_summary.csv"), index=False)

# Efficient frontier
targets = np.linspace(mu.min(), mu.max(), 50)
frontier_rows = []
for target in targets:
    cons = [
        {"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "eq", "fun": lambda w, t=target: w @ mu - t}
    ]
    res = minimize(portfolio_vol, x0, method="SLSQP", bounds=bounds, constraints=cons)
    if res.success:
        frontier_rows.append([target, portfolio_vol(res.x)])
frontier = pd.DataFrame(frontier_rows, columns=["Return", "Volatility"])
frontier.to_csv(os.path.join(OUT, "efficient_frontier.csv"), index=False)

# -----------------------------
# Monte Carlo simulation
# -----------------------------
rng = np.random.default_rng(MONTE_CARLO_SEED)
terminal = np.prod(1 + rng.normal(port.mean(), port.std(ddof=1), (MC_PATHS, MC_DAYS)), axis=1)
mc_summary = pd.DataFrame({
    "Statistic": ["5th Percentile", "Median", "95th Percentile", "Probability of Loss"],
    "Value": [np.quantile(terminal, .05), np.median(terminal), np.quantile(terminal, .95), np.mean(terminal < 1)]
})
pd.DataFrame({"Terminal_Wealth": terminal}).to_csv(os.path.join(OUT, "monte_carlo_terminal_wealth.csv"), index=False)
mc_summary.to_csv(os.path.join(OUT, "monte_carlo_summary.csv"), index=False)

# -----------------------------
# Stress tests
# -----------------------------
asset_betas = np.array([beta_of(R[a], B) for a in ASSETS])
scenarios = {"Market -20%": -.20, "Market -10%": -.10, "Market -5%": -.05,
             "Market +5%": .05, "Market +10%": .10, "Market +20%": .20}
stress = pd.DataFrame([
    [name, shock, W0 @ (asset_betas * shock)]
    for name, shock in scenarios.items()
], columns=["Scenario", "Market_Shock", "Estimated_Portfolio_Return"])
stress.to_csv(os.path.join(OUT, "stress_tests.csv"), index=False)

# -----------------------------
# Rolling analytics
# -----------------------------
rolling = pd.DataFrame(index=port.index)
rolling["Rolling_63D_Volatility"] = port.rolling(63).std() * np.sqrt(ANN)
rolling["Rolling_126D_Volatility"] = port.rolling(126).std() * np.sqrt(ANN)
rolling["Rolling_252D_Beta"] = port.rolling(252).cov(B) / B.rolling(252).var()
rolling.to_csv(os.path.join(OUT, "rolling_analytics.csv"))

# -----------------------------
# Charts
# -----------------------------
plt.figure(figsize=(10, 6))
plt.plot((1 + port).cumprod(), label="Portfolio")
plt.plot((1 + B).cumprod(), label=BENCHMARK)
plt.title("Portfolio vs NIFTY 50 — Cumulative Growth")
plt.xlabel("Date"); plt.ylabel("Growth of ₹1"); plt.legend(); plt.grid(alpha=.25); plt.tight_layout()
plt.savefig(os.path.join(OUT, "01_cumulative_performance.png"), dpi=180); plt.close()

plt.figure(figsize=(10, 5))
plt.plot(dd)
plt.title("Portfolio Drawdown"); plt.xlabel("Date"); plt.ylabel("Drawdown"); plt.grid(alpha=.25); plt.tight_layout()
plt.savefig(os.path.join(OUT, "02_drawdown.png"), dpi=180); plt.close()

plt.figure(figsize=(10, 5))
plt.plot(rolling["Rolling_63D_Volatility"], label="63-day")
plt.plot(rolling["Rolling_126D_Volatility"], label="126-day")
plt.title("Rolling Annualized Volatility"); plt.legend(); plt.grid(alpha=.25); plt.tight_layout()
plt.savefig(os.path.join(OUT, "03_rolling_volatility.png"), dpi=180); plt.close()

plt.figure(figsize=(8, 6))
plt.scatter(B, port, alpha=.25)
plt.title("Portfolio vs NIFTY 50 Daily Returns"); plt.xlabel("NIFTY 50"); plt.ylabel("Portfolio"); plt.grid(alpha=.2); plt.tight_layout()
plt.savefig(os.path.join(OUT, "04_beta_scatter.png"), dpi=180); plt.close()

plt.figure(figsize=(9, 6))
plt.hist(port, bins=50, edgecolor="black")
plt.axvline(-historical_var(port), linestyle="--", label="95% VaR threshold")
plt.title("Portfolio Daily Return Distribution"); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(OUT, "05_var_distribution.png"), dpi=180); plt.close()

plt.figure(figsize=(9, 6))
plt.plot(frontier["Volatility"], frontier["Return"], label="Efficient Frontier")
plt.scatter(portfolio_vol(W0), W0 @ mu, label="Current")
plt.scatter(portfolio_vol(minv.x), minv.x @ mu, label="Min Vol")
plt.scatter(portfolio_vol(maxs.x), maxs.x @ mu, label="Max Sharpe")
plt.xlabel("Annual Volatility"); plt.ylabel("Annual Return"); plt.title("Efficient Frontier"); plt.legend(); plt.grid(alpha=.2); plt.tight_layout()
plt.savefig(os.path.join(OUT, "06_efficient_frontier.png"), dpi=180); plt.close()

plt.figure(figsize=(9, 6))
plt.hist(terminal, bins=60, edgecolor="black")
plt.title("Monte Carlo: 1-Year Terminal Wealth"); plt.xlabel("Terminal Wealth"); plt.tight_layout()
plt.savefig(os.path.join(OUT, "07_monte_carlo.png"), dpi=180); plt.close()

plt.figure(figsize=(9, 6))
plt.bar(ASSETS, W0)
plt.title("Current Portfolio Weights"); plt.ylabel("Weight"); plt.xticks(rotation=45, ha="right"); plt.tight_layout()
plt.savefig(os.path.join(OUT, "08_portfolio_weights.png"), dpi=180); plt.close()

# -----------------------------
# Excel dashboard/report
# -----------------------------
xlsx = os.path.join(OUT, "portfolio_risk_performance_report.xlsx")
with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
    metrics.to_excel(writer, sheet_name="KPIs", index=False)
    asset_stats.to_excel(writer, sheet_name="Asset Stats", index=False)
    corr.to_excel(writer, sheet_name="Correlation")
    risk_contribution.to_excel(writer, sheet_name="Risk Contribution", index=False)
    attr.to_excel(writer, sheet_name="Return Attribution", index=False)
    optimized.to_excel(writer, sheet_name="Optimized Weights", index=False)
    optimization_summary.to_excel(writer, sheet_name="Optimization Summary", index=False)
    frontier.to_excel(writer, sheet_name="Efficient Frontier", index=False)
    stress.to_excel(writer, sheet_name="Stress Tests", index=False)
    mc_summary.to_excel(writer, sheet_name="Monte Carlo", index=False)
    rolling.tail(500).to_excel(writer, sheet_name="Rolling Analytics")

# -----------------------------
# Executive summary
# -----------------------------
summary = f"""# Portfolio Risk & Performance — Executive Summary

**Data period:** {prices.index.min().date()} to {prices.index.max().date()}  
**Portfolio:** Reliance 15%, HDFC Bank 15%, TCS 15%, Infosys 10%, ITC 10%, Larsen & Toubro 15%, Sun Pharma 10%, Bharti Airtel 10%  
**Benchmark:** NIFTY 50  
**Risk-free rate assumption:** {RF:.1%}

## Current portfolio
- Annualized return: **{annual_return(port):.2%}**
- Annualized volatility: **{annual_vol(port):.2%}**
- Sharpe ratio: **{sharpe(port):.2f}**
- Sortino ratio: **{sortino(port):.2f}**
- Maximum drawdown: **{dd.min():.2%}**
- Daily 95% historical VaR: **{historical_var(port):.2%}**
- Daily 95% expected shortfall: **{expected_shortfall(port):.2%}**
- Beta to NIFTY 50: **{beta:.2f}**
- Jensen alpha: **{alpha:.2%}**
- Benchmark correlation: **{port.corr(B):.2f}**

## Optimization
The minimum-volatility and maximum-Sharpe portfolios are provided in `optimized_weights.csv` and summarized in `optimization_summary.csv`.

## Important interpretation
The included price series is **synthetic demonstration data**. The numerical results are suitable for demonstrating the analytics pipeline, not for making real investment decisions. Replace the dataset with documented real market data, verify corporate actions and trading calendars, and revisit assumptions before presenting the results as real-world analysis.
"""
with open(os.path.join(OUT, "EXECUTIVE_SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write(summary)

print(metrics.to_string(index=False))
print(f"\nComplete analysis finished. Outputs: {OUT}")
