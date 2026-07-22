"""Randomisation Check and Covariate Balance Validation Module.

Verifies randomisation success via Standardised Mean Difference (SMD) checks,
Chi-square omnibus test, balance table export, and Love plot visualisation.
"""

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.stats import chi2_contingency, ttest_ind

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR
from src.utils import setup_logger

logger = setup_logger("randomisation_check")


def compute_smd(val_control: np.ndarray, val_treatment: np.ndarray) -> float:
    """Computes Standardised Mean Difference (SMD) for a continuous or binary variable.

    Args:
        val_control: Control group array.
        val_treatment: Treatment group array.

    Returns:
        float: Standardised Mean Difference.
    """
    mean_c, mean_t = np.mean(val_control), np.mean(val_treatment)
    var_c, var_t = np.var(val_control, ddof=1), np.var(val_treatment, ddof=1)
    pooled_sd = np.sqrt((var_c + var_t) / 2.0)
    if pooled_sd < 1e-9:
        return 0.0 if np.isclose(mean_c, mean_t) else float(np.abs(mean_t - mean_c))
    return float(np.abs(mean_t - mean_c) / pooled_sd)


def run_randomisation_check() -> Tuple[pd.DataFrame, str, str]:
    """Executes covariate balance checks across experimental arms and generates reports.

    Returns:
        Tuple[pd.DataFrame, str, str]: Balance table dataframe, CSV path, and PNG plot path.
    """
    logger.info("Loading session dataset for randomisation validation...")
    session_file = PROCESSED_DATA_DIR / "session_data.parquet"
    df = pl.read_parquet(session_file).to_pandas()

    ctrl = df[df["arm"] == "control"]
    trt = df[df["arm"] == "treatment"]

    covariates_data = []

    # 1. Binary / Numeric Covariates
    # Vulnerability Flag
    smd_vuln = compute_smd(ctrl["vulnerability_flag"].values, trt["vulnerability_flag"].values)
    _, p_vuln = ttest_ind(ctrl["vulnerability_flag"], trt["vulnerability_flag"])
    covariates_data.append({
        "Covariate": "Vulnerability Flag",
        "Control_Mean": ctrl["vulnerability_flag"].mean(),
        "Treatment_Mean": trt["vulnerability_flag"].mean(),
        "SMD": smd_vuln,
        "p_value": p_vuln,
        "Balanced_SMD_lt_0_1": smd_vuln < 0.1,
    })

    # Quote Completed Flag
    smd_qc = compute_smd(ctrl["quote_completed"].values, trt["quote_completed"].values)
    _, p_qc = ttest_ind(ctrl["quote_completed"], trt["quote_completed"])
    covariates_data.append({
        "Covariate": "Quote Completed Rate",
        "Control_Mean": ctrl["quote_completed"].mean(),
        "Treatment_Mean": trt["quote_completed"].mean(),
        "SMD": smd_qc,
        "p_value": p_qc,
        "Balanced_SMD_lt_0_1": smd_qc < 0.1,
    })

    # Categorical Factors (Region & Device)
    for cat_col, name in [("region", "Region"), ("device", "Device Type")]:
        categories = df[cat_col].unique()
        for cat in categories:
            c_bin = (ctrl[cat_col] == cat).astype(int).values
            t_bin = (trt[cat_col] == cat).astype(int).values
            smd_cat = compute_smd(c_bin, t_bin)
            _, p_cat = ttest_ind(c_bin, t_bin)
            covariates_data.append({
                "Covariate": f"{name}: {cat}",
                "Control_Mean": c_bin.mean(),
                "Treatment_Mean": t_bin.mean(),
                "SMD": smd_cat,
                "p_value": p_cat,
                "Balanced_SMD_lt_0_1": smd_cat < 0.1,
            })

    balance_df = pd.DataFrame(covariates_data)
    balance_csv = REPORTS_DIR / "balance_table.csv"
    balance_df.to_csv(balance_csv, index=False)
    logger.info(f"Balance table successfully generated and exported to {balance_csv}")

    # 2. Chi-Square Omnibus Tests for Stratification Factors
    contingency_region = pd.crosstab(df["arm"], df["region"])
    chi2_reg, p_reg, _, _ = chi2_contingency(contingency_region)
    logger.info(f"Region Omnibus Chi-Square Test: Chi2={chi2_reg:.4f}, p-value={p_reg:.4f}")

    contingency_device = pd.crosstab(df["arm"], df["device"])
    chi2_dev, p_dev, _, _ = chi2_contingency(contingency_device)
    logger.info(f"Device Omnibus Chi-Square Test: Chi2={chi2_dev:.4f}, p-value={p_dev:.4f}")

    # 3. Love Plot Generation (Covariate Balance Plot)
    plt.figure(figsize=(9, 6))
    y_positions = np.arange(len(balance_df))
    plt.axvline(x=0.1, color="red", linestyle="--", linewidth=1.5, label="Threshold (SMD = 0.1)")
    plt.scatter(balance_df["SMD"], y_positions, color="#1f77b4", s=50, zorder=3)
    plt.yticks(y_positions, balance_df["Covariate"], fontsize=9)
    plt.xlabel("Standardised Mean Difference (SMD)", fontsize=11, fontweight="bold")
    plt.title("Covariate Balance Love Plot (A/A Randomisation Check)", fontsize=13, fontweight="bold", pad=12)
    plt.xlim(-0.01, 0.15)
    plt.grid(axis="x", linestyle=":", alpha=0.7)
    plt.legend(loc="lower right")
    plt.tight_layout()

    love_plot_path = REPORTS_DIR / "love_plot.png"
    plt.savefig(love_plot_path, dpi=300)
    plt.close()
    logger.info(f"Love plot graphic saved to {love_plot_path}")

    return balance_df, str(balance_csv), str(love_plot_path)


def main() -> None:
    """Executes randomisation balance checks."""
    run_randomisation_check()


if __name__ == "__main__":
    main()
