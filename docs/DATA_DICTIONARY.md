# Data Dictionary

## Input: `data/market_prices_demo.csv`

| Field | Meaning | Expected type | Validation |
|---|---|---|---|
| `Date` | Observation date | Date | Unique, sorted after preprocessing |
| `RELIANCE` | Reliance Industries price series | Numeric | Positive |
| `HDFCBANK` | HDFC Bank price series | Numeric | Positive |
| `TCS` | Tata Consultancy Services price series | Numeric | Positive |
| `INFY` | Infosys price series | Numeric | Positive |
| `ITC` | ITC price series | Numeric | Positive |
| `LT` | Larsen & Toubro price series | Numeric | Positive |
| `SUNPHARMA` | Sun Pharmaceutical price series | Numeric | Positive |
| `BHARTIARTL` | Bharti Airtel price series | Numeric | Positive |
| `NIFTY50` | Benchmark price series | Numeric | Positive |

## Derived datasets

- **Daily returns:** percentage change in each price series.
- **Portfolio return:** weighted sum of constituent daily returns.
- **Asset statistics:** annualized return, volatility, Sharpe ratio and beta.
- **Risk contribution:** component contribution to total portfolio volatility.
- **Return attribution:** weighted contribution of each asset to annualized portfolio return.
- **Rolling analytics:** 63-trading-day rolling volatility and beta.
- **Stress tests:** beta-based portfolio estimates under market shock scenarios.

> The included dataset is synthetic demonstration data. It is not a source of live or historical investment data.
