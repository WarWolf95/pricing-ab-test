# Executive Briefing: UK Motor Insurance Pricing A/B Test Results

**Prepared for**: Head of Pricing, Chief Risk Officer, and Consumer Duty Governance Committee  
**Date**: July 2026  
**Jurisdiction / Regulatory Alignment**: United Kingdom — FCA PS22/9, FG22/5, FG21/1  
**Project Capsule Reference**: `PROJECT_CAPSULE.md`  
**Stakeholder Deliverable**: `excel/pricing_ab_test_dashboard.xlsx`

---

## 1. Executive Verdict & Recommendation

> [!IMPORTANT]
> **VERDICT**: **FULL COMMERCIAL ROLLOUT APPROVED** ✅  
> The two-arm randomised controlled trial (RCT) testing the new granular risk-based pricing model achieved a statistically significant **+0.51 percentage point lift in conversion rate** ($p < 0.001$) while remaining portfolio loss ratio neutral ($54.6\%$ Treatment vs $54.4\%$ FCA benchmark). All **FCA Consumer Duty (PS22/9) vulnerability outcome disparity checks passed** with zero regulatory flags.

---

## 2. Business & Regulatory Context

UK general insurance pricing operates under strict FCA oversight:
- **Consumer Duty (PS22/9 & FG22/5)**: Mandates that firms deliver good outcomes for retail customers, specifically monitoring cross-cutting outcomes for vulnerable customers to prevent disparity.
- **FCA GI Pricing Practices (FG21/1)**: Enforces pricing fairness and transparency across direct and Price Comparison Website (PCW) channels.
- **FCA GI Value Measures (2024)**: Establishes annual industry loss ratio benchmarks ($54.4\%$ for Motor All) to evaluate product fair value.

This A/B test evaluated whether introducing finer risk segmentation and additional rating factors into the motor pricing engine improves conversion elasticity without causing adverse selection or unfair pricing outcomes for vulnerable customer cohorts.

---

## 3. Experimental Design & Methodology

| Parameter | Specification | Real UK Benchmark Calibration |
|-----------|---------------|-------------------------------|
| Design Type | Two-arm parallel RCT (50:50 allocation) | Stratified block randomisation (Region x Device) |
| Sample Size | $N = 124,000$ visitor sessions ($62,000$ per arm) | Calculated via `statsmodels.stats.power.NormalIndPower` |
| Primary Estimand | Average Treatment Effect (ATE) on visitor conversion | Control baseline: $8.50\%$ (FCA GI Pricing Practices) |
| Secondary Estimands | Premium Written, Loss Ratio, Complaints per 1k | ONS Population & ASHE 2024 earnings calibration |
| MDE Target | $+0.50\text{ percentage points}$ lift | $\alpha = 0.05, \text{Power} = 0.80$ |

### Covariate Balance (A/A Check Validation)
- All 15 stratification covariates achieved a Standardised Mean Difference ($\text{SMD} < 0.10$).
- Omnibus Chi-Square test for joint regional independence: $p = 0.742$ (confirming balance).
- Covariate balance Love plot generated at `reports/love_plot.png`.

---

## 4. Key Experimental Findings

### 4.1 Primary Estimands Summary Table

| Metric | Control Arm | Treatment Arm | Observed Difference | 95% Confidence Interval | $p$-value | Significance |
|--------|-------------|---------------|---------------------|-------------------------|-----------|--------------|
| **Conversion Rate** | 8.48% | 8.99% | **+0.51 pp** | [+0.31 pp, +0.71 pp] | $< 0.0001$ | **Statistically Significant** |
| **Average Written Premium** | £587.20 | £596.10 | **+£8.90** (+1.5%) | N/A (Mann-Whitney) | $< 0.001$ | **Statistically Significant** |
| **Portfolio Loss Ratio** | 54.30% | 54.60% | **+0.30 pp** | N/A (Fractional Logit) | 0.412 | Neutral (Margin Preserved) |
| **Complaints / 1k Policies** | 11.2 | 11.5 | **+0.3 per 1k** | N/A (Poisson) | 0.620 | Within SLA Target ($<15.0$) |

### 4.2 Conversion Funnel Dynamics
- **Quote Completion Rate**: Control $88.0\%$ vs Treatment $88.2\%$ ($p = 0.35$).
- **Visitor-to-Purchase Conversion**: Lift concentrated at the quote-to-purchase transition, confirming improved price competitiveness for low-risk quotes.
- Conversion funnel visualised at `reports/conversion_funnel.png`.

---

## 5. Consumer Duty Compliance & Regulatory Governance

To ensure compliance with FCA PS22/9 rules, four strict regulatory checks were performed on the experimental data:

| Audit Check | Regulatory Target | Observed Treatment Value | Status | Governance Notes |
|-------------|-------------------|--------------------------|--------|------------------|
| **Vulnerable Conversion Disparity** | $\le 5.0\%$ relative gap | $1.20\%$ relative gap | **PASS** | No evidence of price exclusion for vulnerable cohorts |
| **Vulnerable Loss Ratio Disparity** | $\le 5.0\%$ relative gap | $1.85\%$ relative gap | **PASS** | Equivalent risk-adjusted value across customer health/resilience profiles |
| **Portfolio Fair Value Assessment** | Loss Ratio $\ge 48.96\%$ ($\ge 90\%$ of FCA benchmark) | $54.60\%$ | **PASS** | Exceeds FCA 2024 Motor Value Measure benchmark ($54.4\%$) |
| **Complaints SLA** | $\le 15.0$ complaints / 1k policies | $11.5$ complaints / 1k | **PASS** | Well below internal risk appetite threshold |

---

## 6. Subgroup Analysis & Robustness Checks

### 6.1 Subgroup Heterogeneity (CATE)
- Evaluated across 12 UK regions, vulnerability status, and device types.
- Multiple testing controlled via **Benjamini-Hochberg False Discovery Rate (FDR)** at $\alpha = 0.05$.
- Conversion lift was consistent across all 12 regions ($+0.45\text{ pp}$ to $+0.58\text{ pp}$), with no region exhibiting negative elasticity.
- Subgroup forest plot available at `reports/effect_size_forest.png`.

### 6.2 Sensitivity & Robustness Tests
1. **Intention-To-Treat (ITT)**: $+0.51\text{ pp}$ conversion lift ($N = 124,000$).
2. **Per-Protocol (PP)**: $+0.58\text{ pp}$ conversion lift ($N = 109,120$).
3. **Covariate-Adjusted Model**: Adjusted Odds Ratio $= 1.066$ ($p < 0.0001$).
4. **Bootstrap CIs (1,000 resamples)**: $95\%\text{ CI} = [+0.32\text{ pp}, +0.70\text{ pp}]$.
5. **E-Value Unmeasured Confounding Bound**: $E\text{-value} = 1.34$, demonstrating robustness to potential unobserved traffic shifts.

---

## 7. Next Steps & Implementation Roadmap

1. **Deployment Execution**: Transition 100% of live PCW and Direct traffic to the granular risk pricing model.
2. **Monitoring & Governance**: Implement weekly automated Consumer Duty disparity alerts within live analytics infrastructure.
3. **FCA Regulatory Reporting**: Submit summary findings to the Risk & Conduct Committee for inclusion in the annual Consumer Duty Board Assessment.
