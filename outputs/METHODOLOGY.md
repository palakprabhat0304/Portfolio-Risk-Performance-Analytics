# Methodology & Assumptions

## Data
- Period: 2022-01-03 to 2025-12-31
- Frequency: daily observations
- Assets: RELIANCE, HDFCBANK, TCS, INFY, ITC, LT, SUNPHARMA, BHARTIARTL
- Benchmark: NIFTY50
- Source in this package: synthetic demonstration dataset

## Performance
The headline **annualized return is geometric (CAGR)**. Volatility is the sample standard deviation × √252. Sharpe, Sortino and Jensen alpha use the **arithmetic** mean daily return × 252 as the return input, so they differ slightly from a Sharpe computed on the geometric headline return.

## Risk
- Sharpe = (arithmetic mean daily return × 252 − 6.0%) / annualized volatility
- Sortino uses the daily risk-free target as the downside threshold.
- Historical VaR uses the 5th percentile of daily returns.
- Expected Shortfall averages returns below that VaR threshold.
- Beta is covariance with NIFTY 50 divided by benchmark variance.
- Jensen alpha uses the CAPM-style excess-return relation.

## Optimization
The base model allows long-only weights from 0% to 100% with weights summing to 100%. The practical version adds a **30% maximum position cap** to reduce concentration.

## Monte Carlo
10,000 one-year paths are simulated using the portfolio's historical mean and standard deviation with independent normally distributed daily returns. This is a simplified teaching model and does not model volatility clustering, fat tails, serial correlation, or regime changes.

## Stress testing
Scenario returns are estimated using portfolio beta × market shock. This is a linear approximation and should not be interpreted as a full nonlinear stress model.

## Limitations
The data is synthetic. Corporate actions, dividends, transaction costs, taxes, liquidity, survivorship bias, parameter uncertainty, and out-of-sample validation are not modeled.
