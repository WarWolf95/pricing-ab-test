# Pricing A/B Test Project Capsule

This capsule is the single-source-of-truth for the Pricing Elasticity A/B Test project. Read this first before writing any code.

---

## 1. Executive Summary

A UK motor insurer tests whether a more granular risk-based pricing model improves conversion rates without adversely affecting portfolio loss ratios. This is a two-arm randomised controlled trial (RCT) with a 50:50 split.

- **Treatment**: New granular pricing model (more rating factors, finer risk segmentation)
- **Control**: Current pricing model
- **Primary metric**: Conversion rate (visitor-to-quote-to-purchase funnel)
- **Secondary metric**: Loss ratio (claims paid / premium written) — benchmarked against FCA GI Value Measures
- **Guardrail metric**: Vulnerable customer conversion disparity (Consumer Duty compliance)

---

## 2. Domain Background

### 2.1 UK Motor Insurance Pricing Context

- UK motor insurance is a ~£20bn GWP market regulated by the FCA under Consumer Duty (PS22/9).
- **Pricing Practices (FG21/1)**: Firms must ensure pricing is fair across all customer cohorts, particularly vulnerable customers.
- **GI Value Measures**: FCA publishes annual claims ratios, claims acceptance rates, and average premiums by product category. These serve as industry benchmarks.
- **Price Comparison Websites (PCWs)**: ~60% of motor insurance is distributed via PCWs (ComparetheMarket, MoneySuperMarket, GoCompare, Confused.com). Conversion rates on PCWs are typically 5-15%.

### 2.2 Why This Matters

Pricing optimisation is the single highest-ROI analytical activity in a general insurer. A 1% improvement in conversion rate at constant loss ratio can add £millions to top line. But underpricing risks regulatory breach (Fair Value under Consumer Duty) and adverse selection.

---

## 3. Data Strategy

### 3.1 Real UK Public Data Sources

| Dataset | Source | File | Use |
|---------|--------|------|-----|
| FCA GI Value Measures 2024 | FCA | `data/raw/fca_gi_value_measures_2024.xlsx` | Loss ratio benchmarks by product, claims frequency, claims acceptance rates |
| FCA General Insurance Pricing Practices Data 2023 | FCA (occasional paper) | `data/raw/fca_gi_pricing_data.csv` | Premium distributions, conversion rate ranges by channel, price elasticity references |
| ONS Population Mid-2024 | ONS | `data/raw/ons_population_england_wales_mid2024.xlsx` | Regional demographic weights for customer profile calibration |
| ONS ASHE 2024 (SOC 4-digit) | ONS via Nomis API | `data/raw/ons_ashe_2024.csv` | Median earnings by occupation (proxy for income band in pricing models) |
| ONS RPI / CPI | ONS | `data/raw/ons_cpi_2024.csv` | Inflation adjustment for claim cost calibration |

### 3.2 Simulated Experimental Data

Experimental data (visitor sessions, quotes, purchases, claims) is simulated because no insurer publishes this data. Simulation is calibrated to:

| Parameter | Calibration Source | Target Value |
|-----------|-------------------|--------------|
| Base conversion rate | FCA GI Pricing Practices 2023 + industry benchmarks (Oxbow Partners, EY GI surveys) | 8.5% (control) |
| Minimum detectable effect | Cohen's d = 0.1 (realistic for pricing tests) | 0.5 percentage point lift |
| Sample size per arm | Power analysis (80% power, 5% significance, two-sided) | ~62,000 visitors per arm |
| Premium distribution (control) | FCA GI Value Measures + ONS regional income weights | Log-normal, mean £587, sd £230 |
| Claims frequency | FCA GI Value Measures — Motor (All) | 4.9% annual |
| Claims acceptance rate | FCA GI Value Measures — Motor (All) | 98.3% |
| Average claim cost | FCA GI Value Measures + ONS ASHE repair cost proxy | £2,850 |
| Vulnerability rate | FCA Financial Lives Survey 2024 | 47% of customers show at least one vulnerability indicator |
| Vulnerability distribution | ONS health data + FCA Financial Lives | Health: 32%, Resilience: 28%, Life Events: 22%, Capability: 18% |
| Treatment effect on conversion | Assumed lift (conservative) | +0.5 pp (relative lift ~5.9%) |
| Treatment effect on loss ratio | Assumed neutral (aim is margin-neutral) | +0 to +1 pp |

### 3.3 Data Provenance Classification (mirroring existing repos)

```
Tier 1: Real Public Data — FCA GI Value Measures, FCA Pricing Practices, ONS population, ONS ASHE, ONS CPI
Tier 2: Calibrated Simulated Data — Visitor sessions, quotes, purchases, claims
         Calibrated to Tier 1 distributions via parametric sampling (log-normal, Bernoulli, Poisson)
Tier 3: Analytical Outputs — Power analysis tables, balance tables, hypothesis test results, effect size estimates
Tier 4: Stakeholder Delivery — Excel workbook with formatted dashboards, what-if scenarios, executive summary
```

---

## 4. Experimental Design

### 4.1 Design Summary

| Parameter | Value |
|-----------|-------|
| Design type | Two-arm, parallel, randomised controlled trial |
| Unit of randomisation | Visitor session (unique session_id) |
| Allocation ratio | 50:50 |
| Primary estimand | Average Treatment Effect (ATE) on conversion rate |
| Secondary estimands | ATE on premium written, ATE on loss ratio, ATE on complaints per 1k policies |
| Guardrail estimands | ATE on vulnerable-to-non-vulnerable conversion disparity |
| Randomisation method | Stratified block randomisation by region + device type (desktop/mobile) |
| Stratification factors | Region (12 UK regions from ONS), Device type (Desktop / Mobile / Tablet) |
| Block size | Random blocks of size 4, 6, 8 (to prevent predictability) |

### 4.2 Sample Size Calculation

Standard two-sample z-test for proportions:

```
n = (Z_{alpha/2} + Z_beta)^2 * [p1(1-p1) + p2(1-p2)] / (p2 - p1)^2
```

| Parameter | Value |
|-----------|-------|
| Alpha (two-sided) | 0.05 |
| Power (1 - beta) | 0.80 |
| Control conversion rate (p1) | 0.085 |
| Minimum detectable effect | 0.005 (0.5 pp) |
| Treatment conversion rate (p2) | 0.090 |
| Required n per arm | ~62,000 |
| Total visitors required | ~124,000 |
| Duration at 10,000 visitors/week | ~12-13 weeks |

Implementation: `src/power_analysis.py` using `statsmodels.stats.power.NormalIndPower` and `statsmodels.stats.proportion.samplesize_proportions_2indep_onetail`.

### 4.3 Randomisation Check (A/A Test Validation)

Before analyzing the treatment effect, verify randomisation worked:

| Check | Method | Threshold |
|-------|--------|-----------|
| Balance table | Standardised mean difference (SMD) for all covariates | SMD < 0.1 for all |
| Omnibus test | Chi-square test of independence on stratified factors | p > 0.05 |
| Covariate balance plot | Love plot (coefficient plot) | Visual inspection |
| Joint test | Logistic regression of treatment on all covariates | F-test p > 0.05 (or likelihood ratio test) |

Implementation: `src/randomisation_check.py` — outputs `reports/balance_table.csv`, `reports/love_plot.png`

---

## 5. Statistical Methodology

### 5.1 Primary Analysis

| Metric | Method | Implementation |
|--------|--------|----------------|
| Conversion rate (binary) | Two-sample z-test for proportions | `statsmodels.stats.proportion.proportions_ztest` |
| | Pearson chi-square test | `scipy.stats.chi2_contingency` |
| | Log-binomial regression (adjusted) | `statsmodels.discrete.discrete_model.Logit` |
| Premium per visitor (continuous, skewed) | Mann-Whitney U test | `scipy.stats.mannwhitneyu` |
| | Bootstrap 95% CI (10k resamples) | `numpy.random.choice` + custom function |
| Loss ratio (continuous, bounded [0,1]) | Beta regression | `statsmodels.genmod.generalized_linear_model.GLM` with family=Binomial |
| | Fractional logit (quasi-MLE) | `statsmodels.genmod.generalized_linear_model.GLM` with family=Binomial, cov_type='HC1' |
| Complaints per 1k policies (count) | Poisson / Negative Binomial regression | `statsmodels.discrete.count_model.Poisson` or `NegativeBinomialP` |

### 5.2 Secondary & Subgroup Analyses

| Analysis | Method | Details |
|----------|--------|---------|
| Subgroup: Region | Interaction test in logistic regression | Treatment x Region interaction term, F-test |
| Subgroup: Vulnerability status | Interaction test | Treatment x Vulnerability interaction (Consumer Duty requirement) |
| Subgroup: Device type | Interaction test | Treatment x Device interaction |
| Heterogeneous treatment effects | CATE estimation via logistic regression with full interactions | Visualised with violin plot of predicted treatment effects |
| Multiple testing correction | Benjamini-Hochberg (subgroup analyses only) | Control FDR at 0.05 across the 3 subgroup families |

### 5.3 Sensitivity Analyses

| Analysis | Purpose |
|----------|---------|
| Per-protocol (visitors who completed quote) | Test robustness to attrition |
| Intention-to-treat (all randomised visitors) | Primary analysis |
| With covariate adjustment (logistic regression with region + device + age_band) | Reduce variance, adjust for chance imbalance |
| E-value analysis | Assess robustness to unmeasured confounding |
| Non-parametric bootstrap (10k samples) | Robust SEs, no distributional assumptions |
| MDR (Minimum Detectable Rate) re-estimation | Post-hoc power using observed control rates |

### 5.4 Consumer Duty Compliance Checks

| Check | Threshold | Regulatory Reference |
|-------|-----------|---------------------|
| Vulnerable conversion disparity | < 5% relative difference in conversion rate between vulnerable and non-vulnerable across arms | FCA PS22/9, FG22/5 |
| Vulnerable loss ratio disparity | < 5% relative difference | FCA PS22/9, FG22/5 |
| Fair value assessment | Portfolio loss ratio > FCA benchmark (54.4% for Motor) | FCA GI Value Measures |
| Complaints per 1k policies | < 15.0 per 1k | Internal SLA (from consumer-duty project) |

---

## 6. Technical Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Language | Python 3.10+ | Matches existing projects, type-annotated, PEP 8 |
| Data manipulation | Polars >= 0.20 | High-performance, consistent with Credit Risk project |
| Numerical | NumPy >= 1.26 | Standard |
| Statistics | SciPy >= 1.11, statsmodels >= 0.14 | Power analysis, hypothesis tests, regression models |
| Visualisation | Matplotlib >= 3.8, Seaborn >= 0.13 | Love plots, effect size plots, conversion funnel |
| Excel output | openpyxl >= 3.1 | Programmatic Excel workbook generation with formatting |
| Spreadsheet automation | xlsxwriter (for charts in Excel) | Embedded charts in stakeholder workbook |
| Testing | pytest >= 7.4 | Data quality tests, statistical sanity checks |
| CI/CD | GitHub Actions | Automate test run on push |
| Data storage | SQLite (or DuckDB) | Lightweight, reproducible |

### Dependencies (`requirements.txt`)

```
polars>=0.20.0
numpy>=1.26.0
scipy>=1.11.0
statsmodels>=0.14.0
matplotlib>=3.8.0
seaborn>=0.13.0
pandas>=2.1.0
openpyxl>=3.1.0
xlsxwriter>=3.2.0
pytest>=7.4.0
requests>=2.31.0
```

---

## 7. Directory Structure

```
pricing_ab_test/
├── data/
│   ├── raw/
│   │   ├── fca_gi_value_measures_2024.xlsx    # Real: FCA GI Value Measures 2024
│   │   ├── fca_gi_pricing_data.csv             # Real: FCA GI Pricing Practices
│   │   ├── ons_population_england_wales_mid2024.xlsx  # Real: ONS population
│   │   └── ons_ashe_2024.csv                   # Real: ONS ASHE via Nomis
│   └── processed/
│       ├── experimental_design_params.json     # All simulation parameters
│       ├── session_data.parquet                # Simulated visitor sessions
│       ├── claims_data.parquet                 # Simulated claims
│       └── complaints_data.parquet             # Simulated complaints
├── src/
│   ├── __init__.py
│   ├── config.py                               # All parameters, thresholds, paths
│   ├── utils.py                                # Shared utilities, logging, helpers
│   ├── fetch_fca_data.py                       # Download FCA datasets
│   ├── fetch_ons_data.py                       # Download ONS datasets
│   ├── simulate_experiment.py                  # Generate experimental data (calibrated)
│   ├── power_analysis.py                       # Pre-experiment sample size & MDE
│   ├── randomisation_check.py                  # Balance tables & love plots
│   ├── primary_analysis.py                     # Hypothesis tests & effect sizes
│   ├── subgroup_analysis.py                    # Heterogeneous effects & interactions
│   ├── consumer_duty_checks.py                 # Vulnerability disparity & fair value
│   ├── sensitivity_analysis.py                 # E-value, bootstrap, covariate adjustment
│   └── build_excel_dashboard.py                # Generate stakeholder Excel workbook
├── tests/
│   ├── __init__.py
│   ├── test_power_analysis.py                  # Reproduce known sample sizes
│   ├── test_randomisation.py                   # Balance check statistical tests
│   ├── test_analysis.py                        # Effect size consistency
│   └── test_data_quality.py                    # Null checks, range checks, calibration
├── reports/
│   ├── balance_table.csv                       # Covariate balance summary
│   ├── effect_sizes.csv                        # All ATE estimates with CIs
│   ├── subgroup_results.csv                    # Subgroup ATEs
│   ├── love_plot.png                           # Covariate balance love plot
│   ├── conversion_funnel.png                   # Conversion funnel by arm
│   ├── effect_size_forest.png                  # Forest plot of ATEs by subgroup
│   └── executive_briefing.md                   # Written for Head of Pricing / Risk Committee
├── excel/
│   └── pricing_ab_test_dashboard.xlsx          # Stakeholder-ready Excel workbook
├── .github/
│   └── workflows/
│       └── ci.yml                              # GitHub Actions: install -> test
├── PROJECT_CAPSULE.md                          # This file
├── README.md                                   # Project overview & quickstart
└── requirements.txt                            # Python dependencies
```

---

## 8. Pipeline Orchestration

The pipeline runs as a sequence of independent steps:

```
Step 1: fetch_fca_data.py        — Download FCA GI Value Measures + Pricing Practices data
Step 2: fetch_ons_data.py        — Download ONS population + ASHE data
Step 3: power_analysis.py        — Compute required sample size, save to reports/
Step 4: simulate_experiment.py   — Generate session/claims data calibrated to real distributions
Step 5: randomisation_check.py   — Balance tables, love plot, test randomisation success
Step 6: primary_analysis.py      — Hypothesis tests, effect sizes, ATEs
Step 7: subgroup_analysis.py     — Heterogeneous treatment effects by region/vulnerability/device
Step 8: consumer_duty_checks.py   — Vulnerability disparity, fair value assessment
Step 9: sensitivity_analysis.py   — E-value, bootstrap, covariate adjustment
Step 10: build_excel_dashboard.py — Generate stakeholder Excel workbook
```

Each step is independently callable (`python -m src.step_name`).

Orchestrator script: `run_pipeline.py` at the project root.

---

## 9. Excel Deliverable Specification

### `excel/pricing_ab_test_dashboard.xlsx` — Structure

#### Sheet 1: Executive Summary
- KPI cards (conversion rate, premium, loss ratio — both arms with difference)
- Traffic light RAG status (green/amber/red vs. thresholds)
- 1-paragraph recommendation text
- Date range, sample size, test duration

#### Sheet 2: Experimental Design
- Power analysis parameters (table)
- Sample size by arm (table)
- Randomisation strata (table)
- Pre-registered analysis plan (text box)
- FCA regulatory context (text box)

#### Sheet 3: Balance Table
- Covariate, Control mean, Treatment mean, SMD, p-value (table)
- Conditional formatting: SMD > 0.1 highlighted red

#### Sheet 4: Primary Results
- Metric | Control | Treatment | Difference | 95% CI | p-value | Significant? | Interpretation
- Conversion rate, Avg premium, Loss ratio, Complaints per 1k
- Conditional formatting: significant results bold green

#### Sheet 5: Subgroup Analysis
- Subgroup | Metric | ATE | 95% CI | p-value | BH-adjusted p | Significant?
- By region (12 rows), by vulnerability (2 rows), by device (3 rows)
- Conditional formatting: BH-adjusted p < 0.05 highlighted green

#### Sheet 6: Consumer Duty Compliance
- Metric | Control | Treatment | Threshold | Pass/Fail | Regulatory note
- Vulnerability conversion disparity, Vulnerability loss ratio disparity, Fair value (loss ratio vs FCA benchmark), Complaints per 1k

#### Sheet 7: Sensitivity Analysis
- Analysis method | ATE | 95% CI | Width | Notes
- ITT, PP, adjusted (logistic), bootstrap, E-value

#### Sheet 8: Raw Data (hidden)
- session_id | arm | converted | region | device | vulnerability_flag | age_band | premium | claims_flag | claim_amount
- Used for "what-if" analysis by technically proficient stakeholders

### Implementation Notes for Excel Generation
- Use `openpyxl` for cell-level formatting (borders, fills, fonts, conditional formatting)
- Use `xlsxwriter` for embedded chart objects (conversion funnel bar chart, forest plot, love plot)
- All numbers formatted with appropriate UK number format (`£#,##0.00`, `#,##0.0%`, `#,##0`)
- Sheet tab colours: green (summary), blue (design), orange (balance), green (results), yellow (subgroup), red (compliance), grey (sensitivity)
- Hidden raw data sheet with grey tab colour
- Protected structure (no sheet deletion) but unlocked cells for what-if scenario testing on Sheet 8

---

## 10. Deliverables Checklist

| Deliverable | Format | Location |
|-------------|--------|----------|
| Power analysis report | CSV + console output | `reports/power_analysis.csv`, logged in stdout |
| Balance table | CSV | `reports/balance_table.csv` |
| Love plot (covariate balance) | PNG (300dpi) | `reports/love_plot.png` |
| ATE estimates (all metrics) | CSV | `reports/effect_sizes.csv` |
| Subgroup ATE estimates | CSV | `reports/subgroup_results.csv` |
| Conversion funnel chart | PNG (300dpi) | `reports/conversion_funnel.png` |
| Forest plot (subgroup ATEs) | PNG (300dpi) | `reports/effect_size_forest.png` |
| Consumer Duty compliance table | CSV | `reports/consumer_duty_compliance.csv` |
| Executive Briefing | Markdown | `reports/executive_briefing.md` |
| Stakeholder Excel workbook | .xlsx | `excel/pricing_ab_test_dashboard.xlsx` |
| Unit tests (minimum 8) | pytest | `tests/` |

---

## 11. Constraints & Compliance

1. **No PII**: All simulated data. No real customer personal data is used or generated.
2. **FCA Consumer Duty alignment**: The analysis explicitly tests for vulnerable customer outcome disparity (cross-cutting outcome).
3. **UK GDPR compliant**: No data that could identify an individual. All regional/demographic data at aggregate level.
4. **Reproducibility**: Fixed random seed (42). All parameters in `src/config.py`. Pipeline runs end-to-end with `run_pipeline.py`.
5. **Statistical integrity**: Pre-registered analysis plan in `src/config.py`. No p-hacking. Multiple testing correction applied to subgroup analyses.
6. **Production code standards**: PEP 8, type hints, logging, pytest. Mirroring the coding standards in `consumer-duty-analytics` and `Credit_Risk_Analysis`.

---

## 12. References

- FCA PS22/9 Consumer Duty: https://www.fca.org.uk/publication/policy/ps22-9.pdf
- FCA FG22/5 Consumer Duty Guidance: https://www.fca.org.uk/publication/finalised-guidance/fg22-5.pdf
- FCA GI Value Measures 2024: https://www.fca.org.uk/data/general-insurance-value-measures-data
- FCA General Insurance Pricing Practices (FG21/1): https://www.fca.org.uk/publication/finalised-guidance/fg21-1.pdf
- FCA Financial Lives Survey 2024: https://www.fca.org.uk/publication/research/financial-lives-survey-2024.pdf
- ONS ASHE 2024: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours
- ONS Population Estimates: https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration
- Oxbow Partners UK GI Distribution Survey 2024 (industry reference for conversion rates)
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (sample size tables)
- Rosenbaum, P. (2017). *Observation and Experiment* (E-value methodology reference)
