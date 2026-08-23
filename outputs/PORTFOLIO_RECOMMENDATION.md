# Portfolio Recommendation & Decision Page

> **Scope:** analytical recommendation for a portfolio-risk project. The dataset is synthetic and this page is **not investment advice**.

## Executive decision

The current portfolio shows a weak risk-adjusted profile in the supplied demonstration data: annualized return is **-3.81%**, volatility is **17.21%**, Sharpe is **-0.49**, and maximum drawdown is **-42.23%**.

The unconstrained maximum-Sharpe optimizer selects essentially **100% Bharti Airtel**. That is mathematically valid under the model but is **not a diversified implementation recommendation**. It is a useful diagnostic showing that the optimizer is highly sensitive to the estimated return inputs.

A practical maximum-Sharpe version caps every position at 30%. Its modeled return is **5.43%**, volatility **19.99%**, and Sharpe **-0.03**.

## What the analysis says

1. **Return quality needs improvement.** The current portfolio's return is below the assumed 6.0% risk-free rate.
2. **Drawdown is material.** The historical maximum drawdown is -42.23%.
3. **Market dependence is high.** NIFTY 50 correlation is 0.96; beta is 0.73.
4. **Risk is not evenly distributed.** The largest risk contributor is **LT** at 18.4% of total portfolio volatility.
5. **Stress sensitivity is meaningful.**
- **Market -20%**: beta-based estimated portfolio move of **-14.57%**.
- **Market -10%**: beta-based estimated portfolio move of **-7.28%**.
- **Market -5%**: beta-based estimated portfolio move of **-3.64%**.
- **Market +5%**: beta-based estimated portfolio move of **3.64%**.
- **Market +10%**: beta-based estimated portfolio move of **7.28%**.
- **Market +20%**: beta-based estimated portfolio move of **14.57%**.
6. **Concentration remains important.** The practical optimizer places **90.0%** in its three largest positions, so a position cap alone does not guarantee broad diversification.
7. **Monte Carlo downside is material.** The modeled probability of ending below the starting wealth after one year is **58.3%** under the simplified simulation assumptions.

## Recommended use of the optimizers

- Use **Minimum Volatility** as a risk-control benchmark.
- Use **Maximum Sharpe** as an upper-bound return/risk scenario, not an automatic allocation.
- Use the **Practical Maximum Sharpe (30% cap)** as the more defensible optimization example for a diversified portfolio case study.
- Before any real-world conclusion, replace the synthetic data with verified adjusted prices and rerun the model.

## Implementation checklist

- Validate source and adjusted-price methodology.
- Review transaction costs, taxes, liquidity, and turnover.
- Add position and sector constraints appropriate to the mandate.
- Perform out-of-sample/backtest validation.
- Re-estimate expected returns periodically rather than treating historical means as stable forecasts.
