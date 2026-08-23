"""Final polish layer for the Portfolio Risk & Performance Analytics project.
Runs the core analysis, then adds QA, risk flags, practical optimization, an Excel
executive dashboard, methodology/recommendation/interview documents, and a PPT deck.
"""
from pathlib import Path
import os
import sys
import shutil
import textwrap
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"
DATA = BASE / "data" / "market_prices_demo.csv"

# Run the existing core pipeline first.
import complete_analysis  # noqa: F401,E402

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import ColumnDimension
from pptx import Presentation
from pptx.util import Inches, Pt

ASSETS = complete_analysis.ASSETS
BENCHMARK = complete_analysis.BENCHMARK
RF = complete_analysis.RF
ANN = complete_analysis.ANN
W0 = complete_analysis.W0
prices = complete_analysis.prices
R = complete_analysis.R
B = complete_analysis.B
port = complete_analysis.port
covmat = complete_analysis.covmat
mu = complete_analysis.mu


def portfolio_metrics(w):
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ covmat @ w))
    sr = (ret - RF) / vol if vol else np.nan
    return ret, vol, sr

# Practical constrained maximum-Sharpe portfolio: no asset > 30%.
from scipy.optimize import minimize

def neg_sharpe(w):
    ret, vol, _ = portfolio_metrics(w)
    return -(ret - RF) / vol

cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
res = minimize(
    neg_sharpe,
    np.repeat(1 / len(ASSETS), len(ASSETS)),
    method="SLSQP",
    bounds=[(0, 0.30)] * len(ASSETS),
    constraints=[cons],
    options={"maxiter": 2000, "ftol": 1e-12},
)
if not res.success:
    raise RuntimeError(f"Constrained optimization failed: {res.message}")
practical_w = res.x
practical_ret, practical_vol, practical_sr = portfolio_metrics(practical_w)

practical = pd.DataFrame({
    "Asset": ASSETS,
    "Current_Weight": W0,
    "Practical_Max_Sharpe_Weight": practical_w,
})
practical["Weight_Change"] = practical["Practical_Max_Sharpe_Weight"] - practical["Current_Weight"]
practical.to_csv(OUT / "practical_max_sharpe_weights.csv", index=False)

# Risk flags.
asset_stats = pd.read_csv(OUT / "asset_statistics.csv")
risk_contrib = pd.read_csv(OUT / "risk_contribution.csv")
opt = pd.read_csv(OUT / "optimization_summary.csv")
kpis = pd.read_csv(OUT / "portfolio_kpis.csv")
stress = pd.read_csv(OUT / "stress_tests.csv")
mc = pd.read_csv(OUT / "monte_carlo_summary.csv")

kv = dict(zip(kpis["Metric"], kpis["Value"]))
flags = []
def flag(severity, area, finding, threshold, action):
    flags.append({"Severity": severity, "Area": area, "Finding": finding, "Threshold / Trigger": threshold, "Suggested Action": action})

if float(kv["Sharpe Ratio"]) < 0:
    flag("HIGH", "Risk-adjusted return", f"Current Sharpe is {float(kv['Sharpe Ratio']):.2f}.", "Sharpe < 0", "Review portfolio construction and return drivers.")
if float(kv["Annual Return"]) < float(RF):
    flag("HIGH", "Return", f"Annualized return is {float(kv['Annual Return']):.2%}, below the {RF:.1%} risk-free assumption.", "Return < risk-free rate", "Reassess asset mix and assumptions.")
if abs(float(kv["Maximum Drawdown"])) > 0.30:
    flag("HIGH", "Drawdown", f"Maximum drawdown reached {float(kv['Maximum Drawdown']):.2%}.", "|Max drawdown| > 30%", "Add drawdown controls and scenario review.")
if float(kv["Historical VaR 95% (Daily)"]) > 0.02:
    flag("MEDIUM", "VaR", f"Daily 95% historical VaR is {float(kv['Historical VaR 95% (Daily)']):.2%}.", "VaR > 2%", "Monitor daily downside risk and position sizing.")
if float(kv["Benchmark Correlation"]) > 0.90:
    flag("MEDIUM", "Diversification", f"Correlation with NIFTY 50 is {float(kv['Benchmark Correlation']):.2f}.", "Correlation > 0.90", "Do not assume the stock count alone provides strong diversification.")
max_rc = risk_contrib.loc[risk_contrib["Risk_Contribution_%"].idxmax()]
if float(max_rc["Risk_Contribution_%"]) > 0.20:
    flag("MEDIUM", "Risk concentration", f"{max_rc['Asset']} contributes {float(max_rc['Risk_Contribution_%']):.1%} of portfolio volatility.", "Risk contribution > 20%", "Review concentration and rebalance if appropriate.")
if practical_w.max() >= 0.2999:
    flag("INFO", "Optimization", "Practical max-Sharpe solution still reaches the 30% position cap.", "Any weight = 30% cap", "Treat optimizer output as an analytical scenario, not an automatic trade list.")
current_top3 = np.sort(W0)[-3:].sum()
practical_top3 = np.sort(practical_w)[-3:].sum()
if practical_top3 > 0.70:
    flag("MEDIUM", "Concentration", f"The practical optimizer places {practical_top3:.1%} in its three largest positions.", "Top-3 weight > 70%", "Add sector/position constraints if diversification is a mandate.")
flags_df = pd.DataFrame(flags)
flags_df.to_csv(OUT / "risk_flags.csv", index=False)

# QA checks.
checks = []
def check(name, passed, detail):
    checks.append({"Check": name, "Status": "PASS" if passed else "FAIL", "Detail": detail})

check("Required columns", all(c in prices.columns for c in [*ASSETS, BENCHMARK]), "All configured assets and benchmark are present.")
check("Duplicate dates", not prices.index.duplicated().any(), "No duplicate dates after loading.")
check("Positive prices", bool((prices[[*ASSETS, BENCHMARK]] > 0).all().all()), "All retained price observations are positive.")
check("Current weights sum to 100%", np.isclose(W0.sum(), 1), f"Sum = {W0.sum():.6f}")
check("Practical weights sum to 100%", np.isclose(practical_w.sum(), 1), f"Sum = {practical_w.sum():.6f}")
check("Practical max weight <= 30%", practical_w.max() <= 0.3000001, f"Max = {practical_w.max():.4%}")
check("No missing returns", not R[[*ASSETS]].isna().any().any(), "Return matrix contains no missing values after preprocessing.")
check("Risk contributions reconcile", np.isclose(risk_contrib["Risk_Contribution"].sum(), float(kv["Annual Volatility"]), atol=1e-8), "Sum of component risk contributions equals portfolio volatility.")
check("Optimization weights reconcile", np.isclose(pd.read_csv(OUT / "optimized_weights.csv").iloc[:, 1:].sum().values, [1,1,1]).all(), "Current/min-vol/max-Sharpe weight columns each sum to 100%.")
check("Required output files", all((OUT / f).exists() for f in ["portfolio_risk_performance_report.xlsx", "EXECUTIVE_SUMMARY.md", "01_cumulative_performance.png", "06_efficient_frontier.png"]), "Core deliverables are present.")
qa_df = pd.DataFrame(checks)
qa_df.to_csv(OUT / "qa_checks.csv", index=False)
qa_pass = bool((qa_df["Status"] == "PASS").all())

# Scenario interpretation.
scenario_lines = []
for _, row in stress.iterrows():
    scenario_lines.append(f"- **{row['Scenario']}**: beta-based estimated portfolio move of **{row['Estimated_Portfolio_Return']:.2%}**.")
scenario_text = "\n".join(scenario_lines)

# Recommendation document.
recommendation = f"""# Portfolio Recommendation & Decision Page

> **Scope:** analytical recommendation for a portfolio-risk project. The dataset is synthetic and this page is **not investment advice**.

## Executive decision

The current portfolio shows a weak risk-adjusted profile in the supplied demonstration data: annualized return is **{float(kv['Annual Return']):.2%}**, volatility is **{float(kv['Annual Volatility']):.2%}**, Sharpe is **{float(kv['Sharpe Ratio']):.2f}**, and maximum drawdown is **{float(kv['Maximum Drawdown']):.2%}**.

The unconstrained maximum-Sharpe optimizer selects essentially **100% Bharti Airtel**. That is mathematically valid under the model but is **not a diversified implementation recommendation**. It is a useful diagnostic showing that the optimizer is highly sensitive to the estimated return inputs.

A practical maximum-Sharpe version caps every position at 30%. Its modeled return is **{practical_ret:.2%}**, volatility **{practical_vol:.2%}**, and Sharpe **{practical_sr:.2f}**.

## What the analysis says

1. **Return quality needs improvement.** The current portfolio's return is below the assumed {RF:.1%} risk-free rate.
2. **Drawdown is material.** The historical maximum drawdown is {float(kv['Maximum Drawdown']):.2%}.
3. **Market dependence is high.** NIFTY 50 correlation is {float(kv['Benchmark Correlation']):.2f}; beta is {float(kv['Beta']):.2f}.
4. **Risk is not evenly distributed.** The largest risk contributor is **{max_rc['Asset']}** at {float(max_rc['Risk_Contribution_%']):.1%} of total portfolio volatility.
5. **Stress sensitivity is meaningful.**\n{scenario_text}
6. **Concentration remains important.** The practical optimizer places **{practical_top3:.1%}** in its three largest positions, so a position cap alone does not guarantee broad diversification.
7. **Monte Carlo downside is material.** The modeled probability of ending below the starting wealth after one year is **{float(mc.loc[mc['Statistic']=='Probability of Loss','Value'].iloc[0]):.1%}** under the simplified simulation assumptions.

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
"""
(OUT / "PORTFOLIO_RECOMMENDATION.md").write_text(recommendation, encoding="utf-8")

methodology = f"""# Methodology & Assumptions

## Data
- Period: {prices.index.min().date()} to {prices.index.max().date()}
- Frequency: daily observations
- Assets: {', '.join(ASSETS)}
- Benchmark: {BENCHMARK}
- Source in this package: synthetic demonstration dataset

## Performance
Annualized return uses geometric compounding. Volatility uses sample standard deviation multiplied by √252.

## Risk
- Sharpe = (annualized return − {RF:.1%}) / annualized volatility
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
"""
(OUT / "METHODOLOGY.md").write_text(methodology, encoding="utf-8")

interview = f"""# Interview / Viva Guide

## 1. What problem does this project solve?
It measures portfolio return, volatility and downside risk, decomposes risk/return by asset, tests market sensitivity, and compares alternative portfolio allocations.

## 2. Why use the NIFTY 50 as benchmark?
It provides a broad Indian-equity market reference for beta, correlation and relative performance in this case study.

## 3. Why annualize by 252?
The project assumes roughly 252 trading days per year for daily-market data.

## 4. What does the Sharpe ratio tell you?
It measures excess return per unit of total volatility under the assumed {RF:.1%} risk-free rate.

## 5. What is the key risk finding?
The portfolio has a maximum drawdown of {float(kv['Maximum Drawdown']):.2%}, high benchmark correlation of {float(kv['Benchmark Correlation']):.2f}, and a negative Sharpe ratio in the supplied dataset.

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
"""
(OUT / "INTERVIEW_GUIDE.md").write_text(interview, encoding="utf-8")

# Update README with final deliverables and portfolio narrative.
readme = f"""# Portfolio Risk & Performance Analytics

A reproducible portfolio analytics case study for an 8-stock Indian equity portfolio versus the NIFTY 50.

## Executive result

In the supplied **synthetic demonstration dataset**, the current portfolio has annualized return **{float(kv['Annual Return']):.2%}**, volatility **{float(kv['Annual Volatility']):.2%}**, Sharpe **{float(kv['Sharpe Ratio']):.2f}**, maximum drawdown **{float(kv['Maximum Drawdown']):.2%}**, beta **{float(kv['Beta']):.2f}**, and benchmark correlation **{float(kv['Benchmark Correlation']):.2f}**.

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
"""
(BASE / "README.md").write_text(readme, encoding="utf-8")

# QA report.
qa_report = "# Automated QA Report\n\n" + qa_df.to_markdown(index=False) + f"\n\n**Overall status:** {'PASS' if qa_pass else 'FAIL'}\n"
(OUT / "QA_REPORT.md").write_text(qa_report, encoding="utf-8")

# Excel executive dashboard.
dashboard = OUT / "EXECUTIVE_DASHBOARD.xlsx"
shutil.copy2(OUT / "portfolio_risk_performance_report.xlsx", dashboard)
wb = load_workbook(dashboard)
if "Dashboard" in wb.sheetnames:
    del wb["Dashboard"]
ws = wb.create_sheet("Dashboard", 0)
ws.sheet_view.showGridLines = False

# Theme.
navy = "17365D"; blue = "2F75B5"; light = "D9EAF7"; green = "E2F0D9"; red = "FCE4D6"; gray = "F2F2F2"; white = "FFFFFF"
thin = Side(style="thin", color="D9E1F2")

ws.merge_cells("A1:H2")
ws["A1"] = "PORTFOLIO RISK & PERFORMANCE — EXECUTIVE DASHBOARD"
ws["A1"].font = Font(size=20, bold=True, color=white)
ws["A1"].fill = PatternFill("solid", fgColor=navy)
ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

ws["A4"] = "Data period"; ws["B4"] = f"{prices.index.min().date()} to {prices.index.max().date()}"
ws["D4"] = "Benchmark"; ws["E4"] = BENCHMARK
ws["G4"] = "Risk-free"; ws["H4"] = RF
for c in ["A4","D4","G4"]:
    ws[c].font = Font(bold=True, color=navy)
ws["H4"].number_format = "0.0%"

kpi_map = [
    ("A6", "Annual Return", kv["Annual Return"], "0.00%"),
    ("C6", "Annual Volatility", kv["Annual Volatility"], "0.00%"),
    ("E6", "Sharpe Ratio", kv["Sharpe Ratio"], "0.00"),
    ("G6", "Max Drawdown", kv["Maximum Drawdown"], "0.00%"),
    ("A9", "Daily VaR 95%", kv["Historical VaR 95% (Daily)"], "0.00%"),
    ("C9", "Expected Shortfall", kv["Expected Shortfall 95% (Daily)"], "0.00%"),
    ("E9", "Beta", kv["Beta"], "0.00"),
    ("G9", "NIFTY Correlation", kv["Benchmark Correlation"], "0.00"),
]
for cell, label, value, fmt in kpi_map:
    col = ws[cell].column; row = ws[cell].row
    ws.cell(row, col).value = label
    ws.cell(row, col).font = Font(bold=True, color=white)
    ws.cell(row, col).fill = PatternFill("solid", fgColor=blue)
    ws.cell(row, col).alignment = Alignment(horizontal="center")
    v = ws.cell(row+1, col); v.value = value; v.number_format = fmt
    v.font = Font(size=15, bold=True, color=navy)
    v.fill = PatternFill("solid", fgColor=gray)
    v.alignment = Alignment(horizontal="center")
    for cc in range(col, col+1):
        ws.cell(row, cc).border = Border(top=thin,bottom=thin,left=thin,right=thin)
        ws.cell(row+1, cc).border = Border(top=thin,bottom=thin,left=thin,right=thin)

ws["A12"] = "Key conclusions"
ws["A12"].font = Font(size=14, bold=True, color=navy)
conclusions = [
    f"Current Sharpe is {float(kv['Sharpe Ratio']):.2f}; risk-adjusted performance is weak in the demonstration sample.",
    f"Maximum drawdown is {float(kv['Maximum Drawdown']):.2%}; downside risk is material.",
    f"NIFTY 50 correlation is {float(kv['Benchmark Correlation']):.2f}; diversification is limited versus the broad market.",
    f"Unconstrained max-Sharpe optimizer concentrates at {pd.read_csv(OUT/'optimized_weights.csv')['Maximum_Sharpe_Weight'].max():.1%} in one asset.",
    f"30%-capped practical max-Sharpe: return {practical_ret:.2%}, volatility {practical_vol:.2%}, Sharpe {practical_sr:.2f}.",
]
for i, line in enumerate(conclusions, 13):
    ws[f"A{i}"] = "• " + line
    ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=8)
    ws[f"A{i}"].alignment = Alignment(wrap_text=True, vertical="top")

ws["A20"] = "Current vs optimized weights"
ws["A20"].font = Font(size=14, bold=True, color=navy)
for j, h in enumerate(["Asset","Current","Min Vol","Max Sharpe","Practical Max Sharpe"], 1):
    ws.cell(21,j).value=h; ws.cell(21,j).font=Font(bold=True,color=white); ws.cell(21,j).fill=PatternFill("solid",fgColor=blue)
for i, asset in enumerate(ASSETS,22):
    row = practical.iloc[i-22]
    orig = pd.read_csv(OUT / "optimized_weights.csv").iloc[i-22]
    vals=[asset, orig["Current_Weight"], orig["Minimum_Volatility_Weight"], orig["Maximum_Sharpe_Weight"], row["Practical_Max_Sharpe_Weight"]]
    for j,v in enumerate(vals,1):
        ws.cell(i,j).value=v
        if j>1: ws.cell(i,j).number_format="0.0%"

# Dashboard chart.
chart = BarChart(); chart.title="Current Portfolio Weights"; chart.y_axis.title="Weight"; chart.x_axis.title="Asset"; chart.height=7; chart.width=13
cats = Reference(ws, min_col=1, min_row=22, max_row=29)
data = Reference(ws, min_col=2, min_row=21, max_row=29)
chart.add_data(data, titles_from_data=True); chart.set_categories(cats); chart.legend = None
ws.add_chart(chart, "G20")

for col, width in {"A":22,"B":18,"C":18,"D":18,"E":22,"F":5,"G":22,"H":22}.items():
    ws.column_dimensions[col].width = width
ws.freeze_panes = "A6"

# Style all existing report sheets.
for sheet in wb.worksheets[1:]:
    sheet.freeze_panes = "A2"
    sheet.sheet_view.showGridLines = False
    for cell in sheet[1]:
        cell.font = Font(bold=True, color=white)
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.alignment = Alignment(horizontal="center")
    for col_cells in sheet.columns:
        max_len = max(len(str(c.value)) if c.value is not None else 0 for c in col_cells[:50])
        sheet.column_dimensions[get_column_letter(col_cells[0].column)].width = min(max(max_len+2, 12), 28)

wb.save(dashboard)

# Dashboard image for quick portfolio viewing.
import matplotlib.pyplot as plt
plt.figure(figsize=(13, 7))
labels = ["Return","Volatility","Sharpe","Max Drawdown","Beta","Correlation"]
vals = [float(kv["Annual Return"]), float(kv["Annual Volatility"]), float(kv["Sharpe Ratio"]), float(kv["Maximum Drawdown"]), float(kv["Beta"]), float(kv["Benchmark Correlation"])]
plt.bar(labels, vals)
plt.title("Portfolio Risk & Performance — Executive Snapshot")
plt.ylabel("Metric value")
plt.grid(axis="y", alpha=.2)
plt.tight_layout(); plt.savefig(OUT / "DASHBOARD.png", dpi=180); plt.close()

# PowerPoint presentation.
prs = Presentation()
prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)

def add_title(slide, title, subtitle=None):
    slide.shapes.title.text = title
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(28)
    slide.shapes.title.text_frame.paragraphs[0].font.bold = True
    if subtitle:
        tb = slide.shapes.add_textbox(Inches(.8), Inches(1.15), Inches(11.8), Inches(.5))
        p = tb.text_frame.paragraphs[0]; p.text = subtitle; p.font.size = Pt(14)

def add_bullets(slide, bullets, top=1.6):
    box = slide.shapes.add_textbox(Inches(.9), Inches(top), Inches(11.6), Inches(5.2))
    tf=box.text_frame; tf.word_wrap=True
    for idx,b in enumerate(bullets):
        p=tf.paragraphs[0] if idx==0 else tf.add_paragraph(); p.text=b; p.font.size=Pt(19); p.space_after=Pt(10)

slide=prs.slides.add_slide(prs.slide_layouts[0]); add_title(slide,"Portfolio Risk & Performance Analytics","8-stock Indian equity portfolio vs NIFTY 50 | Final case-study deck")
add_bullets(slide,["Objective: quantify performance, downside risk, market sensitivity, concentration, and optimization trade-offs.","Dataset: synthetic demonstration data — conclusions are illustrative, not investment advice."] ,top=2)

slide=prs.slides.add_slide(prs.slide_layouts[5]); add_title(slide,"Executive snapshot")
add_bullets(slide,[f"Annualized return: {float(kv['Annual Return']):.2%}",f"Annualized volatility: {float(kv['Annual Volatility']):.2%}",f"Sharpe ratio: {float(kv['Sharpe Ratio']):.2f}",f"Maximum drawdown: {float(kv['Maximum Drawdown']):.2%}",f"Beta / NIFTY correlation: {float(kv['Beta']):.2f} / {float(kv['Benchmark Correlation']):.2f}"])

slide=prs.slides.add_slide(prs.slide_layouts[5]); add_title(slide,"Risk diagnosis")
add_bullets(slide,[f"Drawdown is material at {float(kv['Maximum Drawdown']):.2%}.",f"Daily 95% VaR is {float(kv['Historical VaR 95% (Daily)']):.2%}; expected shortfall is {float(kv['Expected Shortfall 95% (Daily)']):.2%}.",f"The portfolio remains highly linked to the broad market (correlation {float(kv['Benchmark Correlation']):.2f}).",f"Largest risk contributor: {max_rc['Asset']} at {float(max_rc['Risk_Contribution_%']):.1%} of total volatility."])

slide=prs.slides.add_slide(prs.slide_layouts[5]); add_title(slide,"Optimization: what the model is really saying")
add_bullets(slide,["Minimum-volatility optimization reduces modeled volatility, but does not necessarily improve expected return.","Unconstrained maximum-Sharpe is essentially a 100% Bharti Airtel solution — a warning about parameter sensitivity and concentration.",f"A 30%-capped practical maximum-Sharpe scenario produces {practical_ret:.2%} expected return, {practical_vol:.2%} volatility, Sharpe {practical_sr:.2f}."])

slide=prs.slides.add_slide(prs.slide_layouts[5]); add_title(slide,"Stress & Monte Carlo")
add_bullets(slide,["Beta-based stress: a -20% market shock implies an estimated portfolio move of -14.57%.",f"Monte Carlo 1-year probability of loss: {float(mc.loc[mc['Statistic']=='Probability of Loss','Value'].iloc[0]):.1%}.","Both are simplified scenario tools and should be supplemented with historical and regime-based stress tests."])

slide=prs.slides.add_slide(prs.slide_layouts[5]); add_title(slide,"Recommendation")
add_bullets(slide,["Do not treat the unconstrained optimizer as an automatic trade list.","Use minimum volatility as a defensive benchmark and the 30%-capped maximum-Sharpe result as the more realistic optimization case study.","For real-world use: replace synthetic data, add transaction costs and constraints, and validate out of sample."])

slide=prs.slides.add_slide(prs.slide_layouts[5]); add_title(slide,"What I would improve next")
add_bullets(slide,["Use verified adjusted prices and documented data lineage.","Add sector, turnover, liquidity, and maximum-position constraints.","Use robust expected-return estimation / shrinkage rather than raw historical means.","Add walk-forward and out-of-sample validation.","Monitor risk limits continuously rather than relying on a single optimization date."])

prs.save(OUT / "Portfolio_Risk_Analytics_Presentation.pptx")

# Copy recommendation as PDF-friendly text if desired by users; markdown is the source of truth.
print("Finalization complete")
print("QA:", "PASS" if qa_pass else "FAIL")
print("Practical max-Sharpe:", practical_ret, practical_vol, practical_sr)
