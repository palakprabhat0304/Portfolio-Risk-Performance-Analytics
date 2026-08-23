# Project Architecture

```text
                +---------------------------+
                | data/market_prices_demo   |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                | src/config.py              |
                | assumptions + portfolio    |
                | + simulation configuration |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                | src/complete_analysis.py   |
                | cleaning + metrics         |
                | attribution + optimization |
                | simulation + charts        |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                | src/finalize_project.py   |
                | practical optimizer        |
                | risk flags + QA            |
                | Excel + PPT + docs         |
                +-------------+-------------+
                              |
                              v
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
      outputs/*.csv      Excel dashboards     PPT + Markdown

                         run_project.py
                              ^
                              |
                    run_project.bat (Windows)
```

## Design principle

The project separates **configuration**, **analysis**, and **reporting** so that assumptions can be changed in one place and the full case study can be regenerated reproducibly.

## Execution order

1. `run_project.py` starts the finalization pipeline.
2. `complete_analysis.py` loads and validates data, computes analytics and produces base outputs.
3. `finalize_project.py` adds constrained optimization, risk flags, QA, dashboards, recommendations and presentation assets.
4. Everything is written to `outputs/`.
