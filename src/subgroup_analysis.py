"""Subgroup Analysis and Heterogeneous Treatment Effect Engine.

Estimates Conditional Average Treatment Effects (CATE) across UK Regions,
Vulnerability Status, and Device Types with Benjamini-Hochberg FDR correction.
Generates subgroup_results.csv and effect_size_forest.png visualisations.
"""

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR
from src.utils import setup_logger

logger = setup_logger("subgroup_analysis")


def run_subgroup_analysis() -> Tuple[pd.DataFrame, str, str]:
    """Evaluates heterogeneous treatment effects by subgroup and exports findings.

    Returns:
        Tuple[pd.DataFrame, str, str]: Subgroup analysis dataframe, CSV path, and PNG forest plot path.
    """
    logger.info("Loading session data for subgroup CATE analysis...")
    sessions_df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet").to_pandas()

    subgroup_records = []

    # Helper function for subgroup z-test
    def evaluate_subgroup(group_col: str, group_val: str, family_name: str) -> None:
        sub_df = sessions_df[sessions_df[group_col] == group_val]
        ctrl_sub = sub_df[sub_df["arm"] == "control"]
        trt_sub = sub_df[sub_df["arm"] == "treatment"]

        n_c, n_t = len(ctrl_sub), len(trt_sub)
        c_conv, t_conv = ctrl_sub["converted"].sum(), trt_sub["converted"].sum()

        p_c = c_conv / n_c if n_c > 0 else 0.0
        p_t = t_conv / n_t if n_t > 0 else 0.0

        ate = p_t - p_c
        se = np.sqrt((p_c * (1 - p_c) / n_c) + (p_t * (1 - p_t) / n_t)) if n_c > 0 and n_t > 0 else 0.0

        z_stat, p_val = proportions_ztest([t_conv, c_conv], [n_t, n_c]) if n_c > 0 and n_t > 0 else (0.0, 1.0)

        ci_low = ate - 1.96 * se
        ci_high = ate + 1.96 * se

        subgroup_records.append({
            "Subgroup_Family": family_name,
            "Subgroup": group_val,
            "Control_N": n_c,
            "Treatment_N": n_t,
            "Control_Conv": p_c,
            "Treatment_Conv": p_t,
            "ATE_pp": ate * 100,
            "SE_pp": se * 100,
            "CI_Lower_pp": ci_low * 100,
            "CI_Upper_pp": ci_high * 100,
            "p_value_raw": p_val,
        })

    # 1. Vulnerability Subgroups
    for v_val in [0, 1]:
        label = "Vulnerable" if v_val == 1 else "Non-Vulnerable"
        evaluate_subgroup("vulnerability_flag", v_val, "Consumer Duty Vulnerability")

    # 2. Device Subgroups
    for dev in sessions_df["device"].unique():
        evaluate_subgroup("device", dev, "Device Type")

    # 3. Regional Subgroups
    for reg in sessions_df["region"].unique():
        evaluate_subgroup("region", reg, "UK Region")

    res_df = pd.DataFrame(subgroup_records)

    # 4. Benjamini-Hochberg FDR Multiple Testing Correction
    p_raw = res_df["p_value_raw"].values
    reject, p_adj, _, _ = multipletests(p_raw, alpha=0.05, method="fdr_bh")

    res_df["p_value_bh_adj"] = p_adj
    res_df["Significant_BH_5pct"] = reject

    csv_path = REPORTS_DIR / "subgroup_results.csv"
    res_df.to_csv(csv_path, index=False)
    logger.info(f"Subgroup CATE analysis results exported to {csv_path}")

    # 5. Forest Plot Visualisation of Subgroup ATEs
    plt.figure(figsize=(10, 8))
    y_pos = np.arange(len(res_df))

    plt.axvline(x=0.0, color="black", linestyle="--", linewidth=1.2)
    plt.axvline(x=0.5, color="green", linestyle=":", linewidth=1.2, label="Target Lift (+0.5 pp)")

    plt.errorbar(
        res_df["ATE_pp"],
        y_pos,
        xerr=[res_df["ATE_pp"] - res_df["CI_Lower_pp"], res_df["CI_Upper_pp"] - res_df["ATE_pp"]],
        fmt="o",
        color="#2b5c8f",
        ecolor="#888888",
        elinewidth=1.5,
        capsize=3,
        zorder=3,
    )

    plt.yticks(y_pos, [f"{r['Subgroup_Family']}: {r['Subgroup']}" for _, r in res_df.iterrows()], fontsize=8.5)
    plt.xlabel("Conditional Average Treatment Effect (ATE % Point Lift)", fontsize=11, fontweight="bold")
    plt.title("Subgroup Forest Plot: Heterogeneous Conversion Treatment Effects", fontsize=13, fontweight="bold", pad=12)
    plt.grid(axis="x", linestyle=":", alpha=0.7)
    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()

    forest_path = REPORTS_DIR / "effect_size_forest.png"
    plt.savefig(forest_path, dpi=300)
    plt.close()
    logger.info(f"Forest plot saved to {forest_path}")

    return res_df, str(csv_path), str(forest_path)


def main() -> None:
    """Executes subgroup analysis engine."""
    run_subgroup_analysis()


if __name__ == "__main__":
    main()
