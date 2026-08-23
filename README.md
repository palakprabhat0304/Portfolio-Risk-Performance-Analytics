# Portfolio Risk & Performance Analytics

A reproducible portfolio analytics case study for an 8-stock Indian equity portfolio versus the NIFTY 50.

## Executive result

In the supplied **synthetic demonstration dataset**, the current portfolio has annualized return **-3.81%**, volatility **17.21%**, Sharpe **-0.49**, maximum drawdown **-42.23%**, beta **0.73**, and benchmark correlation **0.96**.

The unconstrained optimizer is deliberately shown as a diagnostic: it concentrates at approximately 100% in Bharti Airtel. A practical 30%-capped maximum-Sharpe scenario is also included to demonstrate how portfolio constraints change the result.

> **Important:** The included dataset is synthetic. Results must not be presented as real investment recommendations.

## Analysis included

- Performance vs NIFTY 50
- Annualized return, volatility, Sharpe and Sortino
- Maximum drawdown, historical VaR and Expected Shortfall
- Beta, Jensen alpha and correlation
- Asset-level return, volatility, Sharpe and beta
- Correlation matrix
- Risk contribution and return attribution
- Minimum-volatility optimization
- Maximum-Sharpe optimization
- Practical maximum-Sharpe optimization with 30% position cap
- Efficient frontier
- One-year Monte Carlo simulation
- Beta-based market stress testing
- Rolling volatility and beta
- Automated QA checks and risk flags
- Executive Excel dashboard
- Recommendation/decision page
- Methodology and assumptions
- Interview/viva guide
- PowerPoint presentation

## Run

```bash
pip install -r requirements.txt
python src/finalize_project.py
```

All generated outputs are written to `outputs/`.

## Key deliverables

- `outputs/portfolio_risk_performance_report.xlsx` — detailed analysis workbook
- `outputs/EXECUTIVE_DASHBOARD.xlsx` — executive dashboard workbook
- `outputs/PORTFOLIO_RECOMMENDATION.md` — decision page
- `outputs/METHODOLOGY.md` — assumptions and methods
- `outputs/INTERVIEW_GUIDE.md` — interview/viva preparation
- `outputs/QA_REPORT.md` — automated QA results
- `outputs/RISK_FLAGS.csv` / `outputs/risk_flags.csv` — risk alerts
- `outputs/practical_max_sharpe_weights.csv` — constrained optimizer output
- `outputs/Portfolio_Risk_Analytics_Presentation.pptx` — presentation deck
- `outputs/DASHBOARD.png` — visual executive summary

## QA status

The finalization script checks data integrity, weight reconciliation, risk-contribution reconciliation, optimization constraints, and required deliverables. A detailed result is written to `outputs/QA_REPORT.md` and `outputs/qa_checks.csv`.

## Real-world upgrade path

Replace `data/market_prices_demo.csv` with documented adjusted-price data. Record the data source and extraction date, validate corporate actions and dividends, add transaction costs and liquidity constraints, and perform out-of-sample validation before making any investment claim.
