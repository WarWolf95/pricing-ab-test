# Pricing A/B Test: UK Motor Insurance Price Elasticity Experiment

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-PyTest_11_Passed-brightgreen.svg)](tests/)
[![Pipeline](https://img.shields.io/badge/Pipeline-10_Steps-2088FF.svg)]()
[![Regulatory](https://img.shields.io/badge/FCA-PS22%2F9_Consumer_Duty-701B45.svg)](https://www.fca.org.uk/firms/consumer-duty)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF.svg)](.github/workflows/ci.yml)

---

Production-grade A/B testing framework for a UK motor insurer evaluating granular risk-based pricing. Covers the full experimental lifecycle — pre-registered design, power analysis, stratified randomisation, hypothesis testing, heterogeneous treatment effects, and FCA Consumer Duty compliance — delivered as a stakeholder-ready Excel workbook.

## Skills Demonstrated

| Area | What This Project Shows |
|------|------------------------|
| **Experimental Design** | Pre-registered analysis plan, power analysis (NormalIndPower), minimum detectable effect, stratified block randomisation with balance diagnostics |
| **Statistical Inference** | Two-sample z-test, Mann-Whitney U, fractional logit GLM, Poisson regression, bootstrap CIs, Benjamini-Hochberg FDR correction, E-value sensitivity analysis |
| **Regulatory Analytics** | FCA Consumer Duty (PS22/9) vulnerability outcome disparity checks, fair value assessment against FCA GI Value Measures benchmarks |
| **Data Engineering** | Hybrid data strategy (live API with calibrated fallback), polars-based ETL, parquet storage, reproducible pipeline with fixed seed |
| **Stakeholder Delivery** | Programmatic Excel workbook with native formulas, conditional formatting, what-if capability, and executive dashboard |
| **UK Domain Knowledge** | Motor insurance pricing, FCA GI Value Measures (54.4% loss ratio benchmark), ONS ASHE/Nomis regional earnings calibration, vulnerability rate calibration to FCA Financial Lives Survey |

## Quick Start

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py    # Runs all 10 steps end-to-end
python -m pytest tests/   # 11 tests
```

## Outputs

`run_pipeline.py` generates:
- `reports/power_analysis.csv` — Pre-experiment sample size and MDE
- `reports/balance_table.csv` — Covariate balance with SMD checks
- `reports/love_plot.png` — Balance visualisation
- `reports/effect_sizes.csv` — Primary ATEs with CIs and p-values
- `reports/conversion_funnel.png` — Funnel by arm
- `reports/subgroup_results.csv` — CATE by region/vulnerability/device
- `reports/effect_size_forest.png` — Subgroup forest plot
- `reports/consumer_duty_compliance.csv` — Regulatory audit table
- `reports/sensitivity_results.csv` — ITT/PP, bootstrap, E-value
- `reports/executive_briefing.md` — Board-level summary
- `excel/pricing_ab_test_dashboard.xlsx` — 8-sheet stakeholder workbook

## Project Structure

```
pricing_ab_test/
├── src/           # 10 Python modules (power analysis → Excel build)
├── tests/         # 11 pytest unit tests
├── data/raw/      # Real FCA & ONS data (live download with fallback)
├── data/processed/ # Parquet session/claims/complaints data
├── reports/       # CSV tables + PNG charts + executive briefing
├── excel/         # Stakeholder Excel workbook (native formulas)
└── .github/       # CI pipeline
```

## Data Strategy

Tier 1 sources (live download attempted): FCA GI Value Measures, FCA Pricing Practices, ONS Population Estimates, Nomis ASHE API. Falls back to calibrated synthetic data if sources are unavailable.

Full technical specification: `PROJECT_CAPSULE.md`
