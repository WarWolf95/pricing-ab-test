# Pricing A/B Test: UK Motor Insurance Price Elasticity Experiment

[![CI - Pricing A/B Test](https://github.com/WarWolf95/pricing-ab-test/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/WarWolf95/pricing-ab-test/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Data Engine Polars](https://img.shields.io/badge/Data_Engine-Polars-CD792C.svg)](https://pola.rs/)
[![Regulatory Standard FCA PS22/9](https://img.shields.io/badge/FCA_Reg-PS22%2F9_Consumer_Duty-701B45.svg)](https://www.fca.org.uk/firms/consumer-duty)

A production-grade, end-to-end A/B testing and causal inference framework for a UK motor insurer evaluating granular, risk-based pricing elasticity. 

Covers the full experimental lifecycle: pre-registered design, power analysis, stratified randomisation, hypothesis testing, heterogeneous treatment effects (CATE), sensitivity robustness bounds, and FCA Consumer Duty (PS22/9) compliance auditing. Delivered as a native formula-driven stakeholder Excel workbook and automated report suite.

---

## Executive Summary & Primary Results

In a 10-week randomized trial with **124,000 visitor sessions** (62,000 Control, 62,000 Treatment), granular risk-based pricing produced a statistically significant conversion lift while maintaining portfolio risk balance and Consumer Duty compliance:

| Metric | Control | Treatment | ATE (Impact) | 95% Confidence Interval | p-value | Significant (α=0.05) | Test Methodology |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Conversion Rate** | 7.28% | 7.88% | **+0.60 pp** | [+0.31 pp, +0.89 pp] | **p = 6.62e-05** | **Yes (Stat. Sig.)** | Two-sample Proportion Z-test |
| **Average Written Premium** | £586.04 | £594.68 | **+£8.64** | [-£0.66, +£17.76] | p = 0.113 | No | Bootstrap (10k resamples) + Mann-Whitney U |
| **Portfolio Loss Ratio** | 20.51% | 19.38% | **-1.13 pp** | HC1 Robust Bounds | p = 0.834 | No (Favourable) | Fractional Logit GLM (HC1) |
| **Complaints Per 1k Policies** | 11.52 | 9.01 | **-2.51** | Poisson Dispersion Bounds | p = 0.231 | No (Parity) | Poisson GLM Regression |

---

## Visual Showcase & Empirical Diagnostics

### 1. Pre-Experiment Randomisation & Covariate Balance (Love Plot)
Standardised Mean Differences (SMD) across all pre-treatment demographic and vehicle covariates remain strictly within the **±0.05 threshold**, confirming rigorous balance across experimental arms.

![Covariate Balance Love Plot](reports/love_plot.png)

---

### 2. Conversion Funnel by Experimental Arm
Tracking quote initiation, address verification, policy customization, and binding stages. The conversion lift is realized in the final purchasing stage without drop-off distortion.

![Conversion Funnel by Experimental Arm](reports/conversion_funnel.png)

---

### 3. Subgroup Heterogeneous Treatment Effects (CATE Forest Plot)
Conditional Average Treatment Effects across customer segments, evaluated with Benjamini-Hochberg False Discovery Rate (FDR) control at $q=0.05$. Verified zero disparate impact or adverse outcome disparity across FCA vulnerability drivers.

![Subgroup Forest Plot](reports/effect_size_forest.png)

---

## Pre-Experiment Power Analysis

Statistical design parameters pre-registered prior to data collection:

*   **Significance Level ($\alpha$):** 0.05 (Two-sided)
*   **Target Statistical Power ($1 - \beta$):** 0.80 (80%)
*   **Baseline Conversion ($p_1$):** 8.50% (Calibrated from FCA GI Pricing data)
*   **Target Conversion ($p_2$):** 9.00%
*   **Minimum Detectable Effect (MDE):** **0.50 pp** absolute lift
*   **Required Sample Size:** 50,125 per arm (100,250 total)
*   **Planned Sample Size:** **124,000 sessions** (ensuring $>85\%$ power for subgroup analyses)

---

## Regulatory Compliance & Governance (FCA PS22/9)

This framework directly embeds conduct and fairness audits complying with the **FCA Consumer Duty**:
1. **Price & Value:** Evaluates loss ratios against the FCA General Insurance Value Measures benchmark (54.4% industry motor benchmark).
2. **Vulnerability Outcome Parity:** Continuous testing of vulnerable customer cohorts (calibrated to FCA Financial Lives Survey incidence rates) ensuring pricing elasticity does not exploit vulnerable characteristics.
3. **Complaint Disparity:** Poisson regression monitoring of service friction and dissatisfaction rates between arms.

---

## Skills & Architecture

| Area | What This Project Shows |
| :--- | :--- |
| **Experimental Design** | Pre-registered analysis plan, power analysis (`NormalIndPower`), MDE estimation, stratified block randomisation |
| **Statistical Inference** | Two-sample proportion z-test, Mann-Whitney U, fractional logit GLM, Poisson regression, bootstrap CIs, Benjamini-Hochberg FDR, E-value bounds |
| **Regulatory Analytics** | FCA Consumer Duty (PS22/9) vulnerability disparity checks, fair value assessment against FCA GI benchmarks |
| **High-Performance ETL** | Polars-based streaming ETL, Parquet storage, reproducible execution with fixed seeds |
| **Stakeholder Delivery** | Programmatically compiled Excel workbook (`openpyxl`/`xlsxwriter`) with native Excel formulas, what-if modeling, and conditional formatting |

---

## Quick Start & Reproduction

### 1. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate    # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Execute End-to-End Pipeline
Runs all 10 steps sequentially (data ingestion, simulation, hypothesis testing, CATE, Consumer Duty audit, and Excel dashboard generation):
```powershell
python run_pipeline.py
```

### 3. Run Automated PyTest Suite
```powershell
python -m pytest tests/ -v
```

---

## Repository Structure

```
pricing-ab-test/
├── .github/workflows/
│   └── ci.yml                 # Automated GitHub Actions test & pipeline runner
├── data/
│   ├── raw/                   # FCA & ONS regulatory benchmark data
│   └── processed/             # Parquet session, claims, and complaints data
├── excel/
│   └── pricing_ab_test_dashboard.xlsx  # 8-sheet native formula stakeholder workbook
├── reports/
│   ├── power_analysis.csv     # Sample size & MDE parameters
│   ├── balance_table.csv      # Covariate balance diagnostics
│   ├── love_plot.png          # Standardised Mean Difference plot
│   ├── effect_sizes.csv       # Primary ATEs, p-values & CIs
│   ├── conversion_funnel.png  # Funnel progression by arm
│   ├── subgroup_results.csv   # Heterogeneous treatment effects (CATE)
│   ├── effect_size_forest.png # Subgroup forest plot
│   ├── consumer_duty_compliance.csv # FCA audit outcome table
│   ├── sensitivity_results.csv# E-value & bootstrap robustness bounds
│   └── executive_briefing.md  # Board-level executive briefing
├── src/
│   ├── build_excel_dashboard.py
│   ├── consumer_duty_checks.py
│   ├── fetch_fca_data.py
│   ├── fetch_ons_data.py
│   ├── power_analysis.py
│   ├── primary_analysis.py
│   ├── randomisation_check.py
│   ├── sensitivity_analysis.py
│   ├── simulate_experiment.py
│   ├── subgroup_analysis.py
│   └── utils.py
├── tests/                     # 11 unit tests for statistical validity & data schemas
├── LICENSE                    # MIT License
├── PROJECT_CAPSULE.md         # Architecture and technical specification
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

---

## License

This project is licensed under the [MIT License](LICENSE).
