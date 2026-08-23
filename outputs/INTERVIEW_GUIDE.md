# Interview / Viva Guide

## 1. What problem does this project solve?
It measures portfolio return, volatility and downside risk, decomposes risk/return by asset, tests market sensitivity, and compares alternative portfolio allocations.

## 2. Why use the NIFTY 50 as benchmark?
It provides a broad Indian-equity market reference for beta, correlation and relative performance in this case study.

## 3. Why annualize by 252?
The project assumes roughly 252 trading days per year for daily-market data.

## 4. What does the Sharpe ratio tell you?
It measures excess return per unit of total volatility under the assumed 6.0% risk-free rate.

## 5. What is the key risk finding?
The portfolio has a maximum drawdown of -42.23%, high benchmark correlation of 0.96, and a negative Sharpe ratio in the supplied dataset.

## 6. Why is the unconstrained optimizer concentrated?
Because the optimization relies on estimated historical mean returns and permits 100% weight in one asset. The result is a sensitivity diagnostic, not a diversified mandate.

## 7. How did you address that?
I added a practical maximum-Sharpe version with a 30% maximum position size.

## 8. What would you improve next?
Use real adjusted prices, add sector/position/turnover constraints, include transaction costs, use robust or shrinkage return estimates, and validate out of sample.

## 9. What is Monte Carlo's biggest limitation here?
It assumes independent normal daily returns with fixed historical mean and volatility, which understates some real-world tail and regime risks.

## 10. What makes this project portfolio-ready?
It combines reproducible Python analytics, QA checks, risk flags, optimization, stress testing, an executive dashboard, a decision page, and a presentation deck.
