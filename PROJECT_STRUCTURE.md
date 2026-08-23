# Project Structure

```text
Portfolio_Risk_Performance_Analytics_Complete/
├── data/
│   └── market_prices_demo.csv
├── src/
│   ├── config.py
│   ├── complete_analysis.py
│   └── finalize_project.py
├── notebooks/
│   └── Portfolio_Risk_Analytics.ipynb
├── outputs/
│   ├── EXECUTIVE_DASHBOARD.xlsx
│   ├── portfolio_risk_performance_report.xlsx
│   ├── Portfolio_Risk_Analytics_Presentation.pptx
│   ├── DASHBOARD.png
│   ├── portfolio_kpis.csv
│   ├── asset_statistics.csv
│   ├── correlation_matrix.csv
│   ├── risk_contribution.csv
│   ├── return_attribution.csv
│   ├── optimized_weights.csv
│   ├── practical_max_sharpe_weights.csv
│   ├── optimization_summary.csv
│   ├── efficient_frontier.csv
│   ├── monte_carlo_summary.csv
│   ├── stress_tests.csv
│   ├── rolling_analytics.csv
│   ├── RISK_FLAGS.csv
│   ├── qa_checks.csv
│   └── supporting Markdown reports
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   └── REAL_WORLD_CHECKLIST.md
├── tests/
│   └── test_smoke.py
├── run_project.py
├── run_project.bat
├── requirements.txt
├── CHANGELOG.md
├── .gitignore
├── PROJECT_STRUCTURE.md
└── README.md
```

## Execution flow

`run_project.py` → `src/finalize_project.py` → `src/complete_analysis.py` → analytics + optimization + simulation → QA + reporting → `outputs/`.

Configuration is centralized in `src/config.py` so assumptions can be changed without modifying the analytical formulas.
