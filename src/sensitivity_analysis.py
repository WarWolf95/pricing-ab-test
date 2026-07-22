"""Sensitivity Analysis and Robustness Evaluation Engine Module.

Evaluates Intention-to-Treat (ITT) vs Per-Protocol (PP), covariate-adjusted logistic
regression, 1,000 resample bootstrap CIs, and E-value unmeasured confounding sensitivity.
Exports results to reports/sensitivity_results.csv.
"""

from typing import Tuple

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.formula.api as smf

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR
from src.utils import setup_logger

logger = setup_logger("sensitivity_analysis")


def calculate_e_value(rr: float) -> float:
    """Calculates VanderWeele E-value for relative risk to assess unmeasured confounding sensitivity.

    Args:
        rr: Relative Risk ratio.

    Returns:
        float: Calculated E-value.
    """
    if rr < 1.0:
        rr = 1.0 / rr
    return float(rr + np.sqrt(rr * (rr - 1.0)))


def run_sensitivity_analysis() -> Tuple[pd.DataFrame, str]:
    """Executes sensitivity and robustness evaluations and exports summary CSV.

    Returns:
        Tuple[pd.DataFrame, str]: Sensitivity dataframe and output CSV path.
    """
    logger.info("Executing Sensitivity Analysis and Robustness Evaluations...")

    sessions_df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet").to_pandas()
    sessions_df["is_treatment"] = (sessions_df["arm"] == "treatment").astype(int)

    results = []

    # 1. Intention-To-Treat (ITT) — All Randomised Sessions
    ctrl_itt = sessions_df[sessions_df["arm"] == "control"]["converted"]
    trt_itt = sessions_df[sessions_df["arm"] == "treatment"]["converted"]
    n_c_itt, n_t_itt = len(ctrl_itt), len(trt_itt)
    p_ctrl_itt = ctrl_itt.mean()
    p_trt_itt = trt_itt.mean()
    ate_itt = p_trt_itt - p_ctrl_itt
    se_itt = np.sqrt(p_ctrl_itt * (1 - p_ctrl_itt) / n_c_itt + p_trt_itt * (1 - p_trt_itt) / n_t_itt)
    ci_low_itt = (ate_itt - 1.96 * se_itt) * 100
    ci_high_itt = (ate_itt + 1.96 * se_itt) * 100

    results.append({
        "Analysis_Type": "Intention-To-Treat (ITT)",
        "Sample_N": len(sessions_df),
        "ATE_pp": ate_itt * 100,
        "CI_95_pp": f"[{ci_low_itt:+.2f} pp, {ci_high_itt:+.2f} pp]",
        "Notes": "Primary Estimand across all randomised visitor sessions",
    })

    # 2. Per-Protocol (PP) — Visitors Who Completed Quote
    pp_df = sessions_df[sessions_df["quote_completed"] == 1]
    ctrl_pp = pp_df[pp_df["arm"] == "control"]["converted"]
    trt_pp = pp_df[pp_df["arm"] == "treatment"]["converted"]
    n_c_pp, n_t_pp = len(ctrl_pp), len(trt_pp)
    p_ctrl_pp = ctrl_pp.mean()
    p_trt_pp = trt_pp.mean()
    ate_pp = p_trt_pp - p_ctrl_pp
    se_pp = np.sqrt(p_ctrl_pp * (1 - p_ctrl_pp) / n_c_pp + p_trt_pp * (1 - p_trt_pp) / n_t_pp)
    ci_low_pp = (ate_pp - 1.96 * se_pp) * 100
    ci_high_pp = (ate_pp + 1.96 * se_pp) * 100

    results.append({
        "Analysis_Type": "Per-Protocol (PP)",
        "Sample_N": len(pp_df),
        "ATE_pp": ate_pp * 100,
        "CI_95_pp": f"[{ci_low_pp:+.2f} pp, {ci_high_pp:+.2f} pp]",
        "Notes": "Restricted to visitors completing the quote process",
    })

    # 3. Covariate-Adjusted Logistic Regression Model
    logit_mod = smf.logit("converted ~ is_treatment + C(region) + C(device) + C(age_band)", data=sessions_df).fit(disp=0)
    or_adj = np.exp(logit_mod.params["is_treatment"])
    p_val_adj = logit_mod.pvalues["is_treatment"]

    results.append({
        "Analysis_Type": "Covariate-Adjusted Logistic Regression",
        "Sample_N": len(sessions_df),
        "ATE_pp": f"Odds Ratio: {or_adj:.4f}",
        "CI_95_pp": f"p-val: {p_val_adj:.4e}",
        "Notes": "Adjusted for region, device type, and age band",
    })

    # 4. Bootstrap Non-Parametric Re-sampling (1,000 resamples)
    n_boot = 1000
    boot_ates = []
    np.random.seed(42)

    ctrl_vals = sessions_df[sessions_df["arm"] == "control"]["converted"].values
    trt_vals = sessions_df[sessions_df["arm"] == "treatment"]["converted"].values

    for _ in range(n_boot):
        sample_c = np.random.choice(ctrl_vals, size=len(ctrl_vals), replace=True)
        sample_t = np.random.choice(trt_vals, size=len(trt_vals), replace=True)
        boot_ates.append((sample_t.mean() - sample_c.mean()) * 100)

    boot_low = np.percentile(boot_ates, 2.5)
    boot_high = np.percentile(boot_ates, 97.5)
    boot_mean = np.mean(boot_ates)

    results.append({
        "Analysis_Type": "Non-Parametric Bootstrap (1k resamples)",
        "Sample_N": len(sessions_df),
        "ATE_pp": boot_mean,
        "CI_95_pp": f"[{boot_low:+.2f} pp, {boot_high:+.2f} pp]",
        "Notes": "Empirical bootstrap percentile confidence intervals",
    })

    # 5. E-Value Unmeasured Confounding Sensitivity
    rr = p_trt_itt / p_ctrl_itt
    e_val = calculate_e_value(rr)

    results.append({
        "Analysis_Type": "E-Value Unmeasured Confounding Bound",
        "Sample_N": len(sessions_df),
        "ATE_pp": f"E-value = {e_val:.3f}",
        "CI_95_pp": "N/A",
        "Notes": "Minimum confounder RR required to explain away observed treatment effect",
    })

    res_df = pd.DataFrame(results)
    csv_path = REPORTS_DIR / "sensitivity_results.csv"
    res_df.to_csv(csv_path, index=False)
    logger.info(f"Sensitivity analysis report exported to {csv_path}")

    return res_df, str(csv_path)


def main() -> None:
    """Executes sensitivity analysis engine."""
    run_sensitivity_analysis()


if __name__ == "__main__":
    main()
