"""Primary Statistical Analysis Engine Module.

Executes primary hypothesis tests, Average Treatment Effect (ATE) estimation,
confidence interval computation, loss ratio fractional logit modelling, and
generates conversion funnel visualization and effect_sizes.csv.
"""

from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportions_ztest

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR
from src.utils import setup_logger

logger = setup_logger("primary_analysis")


def run_primary_analysis() -> Tuple[pd.DataFrame, str, str]:
    """Executes primary hypothesis tests and exports effect size summaries and funnel chart.

    Returns:
        Tuple[pd.DataFrame, str, str]: Results dataframe, CSV path, and PNG funnel path.
    """
    logger.info("Loading session, claims, and complaints data for primary analysis...")

    sessions_df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet").to_pandas()
    claims_df = pl.read_parquet(PROCESSED_DATA_DIR / "claims_data.parquet").to_pandas()
    complaints_df = pl.read_parquet(PROCESSED_DATA_DIR / "complaints_data.parquet").to_pandas()

    ctrl_sess = sessions_df[sessions_df["arm"] == "control"]
    trt_sess = sessions_df[sessions_df["arm"] == "treatment"]

    n_ctrl = len(ctrl_sess)
    n_trt = len(trt_sess)

    # 1. Primary Estimand: Conversion Rate
    conv_ctrl = ctrl_sess["converted"].sum()
    conv_trt = trt_sess["converted"].sum()

    p_ctrl = conv_ctrl / n_ctrl
    p_trt = conv_trt / n_trt
    ate_conv = p_trt - p_ctrl
    rel_lift_conv = (p_trt - p_ctrl) / p_ctrl

    # Two-sample Z-test for proportions
    z_stat, p_val_conv = proportions_ztest([conv_trt, conv_ctrl], [n_trt, n_ctrl])

    # 95% Confidence Interval for proportion difference
    se_diff = np.sqrt((p_ctrl * (1 - p_ctrl) / n_ctrl) + (p_trt * (1 - p_trt) / n_trt))
    ci_lower_conv = ate_conv - 1.96 * se_diff
    ci_upper_conv = ate_conv + 1.96 * se_diff

    # 2. Average Written Premium (Converted Policies)
    prem_ctrl = ctrl_sess[ctrl_sess["converted"] == 1]["quoted_premium"]
    prem_trt = trt_sess[trt_sess["converted"] == 1]["quoted_premium"]

    mean_prem_c = prem_ctrl.mean()
    mean_prem_t = prem_trt.mean()
    ate_prem = mean_prem_t - mean_prem_c

    # Bootstrap 95% CI for premium difference (10,000 resamples)
    np.random.seed(42)
    boot_diffs = []
    for _ in range(10000):
        boot_c = np.random.choice(prem_ctrl.values, size=len(prem_ctrl), replace=True)
        boot_t = np.random.choice(prem_trt.values, size=len(prem_trt), replace=True)
        boot_diffs.append(boot_t.mean() - boot_c.mean())
    prem_ci_low = np.percentile(boot_diffs, 2.5)
    prem_ci_high = np.percentile(boot_diffs, 97.5)

    mw_stat, p_val_prem = mannwhitneyu(prem_trt, prem_ctrl, alternative="two-sided")

    # 3. Loss Ratio (Claims Paid / Premium Written)
    # Merging claims to converted policies
    policy_df = sessions_df[sessions_df["converted"] == 1].merge(claims_df, on=["session_id", "arm"], how="left")
    policy_df["claim_amount"] = policy_df["claim_amount"].fillna(0.0)

    lr_ctrl_df = policy_df[policy_df["arm"] == "control"]
    lr_trt_df = policy_df[policy_df["arm"] == "treatment"]

    tot_claims_c = lr_ctrl_df["claim_amount"].sum()
    tot_prem_c = lr_ctrl_df["quoted_premium"].sum()
    loss_ratio_c = tot_claims_c / tot_prem_c if tot_prem_c > 0 else 0.0

    tot_claims_t = lr_trt_df["claim_amount"].sum()
    tot_prem_t = lr_trt_df["quoted_premium"].sum()
    loss_ratio_t = tot_claims_t / tot_prem_t if tot_prem_t > 0 else 0.0

    ate_lr = loss_ratio_t - loss_ratio_c

    # Fractional Logit GLM for Loss Ratio (HC1 Robust SEs)
    policy_df["is_treatment"] = (policy_df["arm"] == "treatment").astype(int)
    policy_df["policy_loss_ratio"] = np.clip(policy_df["claim_amount"] / policy_df["quoted_premium"], 0.0, 1.0)

    glm_model = smf.glm(
        formula="policy_loss_ratio ~ is_treatment",
        data=policy_df,
        family=sm.families.Binomial(link=sm.families.links.Logit()),
    ).fit(cov_type="HC1")
    p_val_lr = glm_model.pvalues["is_treatment"]

    # 4. Complaints Per 1k Policies
    comp_merged = sessions_df[sessions_df["converted"] == 1].merge(complaints_df, on=["session_id", "arm"], how="left")
    comp_merged["complaint_flag"] = comp_merged["complaint_flag"].fillna(0)
    comp_merged["is_treatment"] = (comp_merged["arm"] == "treatment").astype(int)

    comp_c = comp_merged[comp_merged["arm"] == "control"]["complaint_flag"]
    comp_t = comp_merged[comp_merged["arm"] == "treatment"]["complaint_flag"]

    rate_comp_c = (comp_c.sum() / len(comp_c)) * 1000
    rate_comp_t = (comp_t.sum() / len(comp_t)) * 1000
    ate_comp = rate_comp_t - rate_comp_c

    poisson_model = smf.glm(
        formula="complaint_flag ~ is_treatment",
        data=comp_merged,
        family=sm.families.Poisson(),
    ).fit()
    p_val_comp = poisson_model.pvalues["is_treatment"]

    # 5. Compile Results Table
    results = [
        {
            "Metric": "Conversion Rate",
            "Control": f"{p_ctrl * 100:.2f}%",
            "Treatment": f"{p_trt * 100:.2f}%",
            "ATE": f"{ate_conv * 100:+.2f} pp",
            "CI_95": f"[{ci_lower_conv * 100:+.2f} pp, {ci_upper_conv * 100:+.2f} pp]",
            "p_value": p_val_conv,
            "Significant_5pct": p_val_conv < 0.05,
            "Test_Method": "Two-sample Proportion Z-test",
        },
        {
            "Metric": "Average Written Premium",
            "Control": f"£{mean_prem_c:.2f}",
            "Treatment": f"£{mean_prem_t:.2f}",
            "ATE": f"£{ate_prem:+.2f}",
            "CI_95": f"[£{prem_ci_low:+.2f}, £{prem_ci_high:+.2f}]",
            "p_value": p_val_prem,
            "Significant_5pct": p_val_prem < 0.05,
            "Test_Method": "Bootstrap (10k resamples) + Mann-Whitney U",
        },
        {
            "Metric": "Portfolio Loss Ratio",
            "Control": f"{loss_ratio_c * 100:.2f}%",
            "Treatment": f"{loss_ratio_t * 100:.2f}%",
            "ATE": f"{ate_lr * 100:+.2f} pp",
            "CI_95": "N/A (Fractional Logit)",
            "p_value": p_val_lr,
            "Significant_5pct": p_val_lr < 0.05,
            "Test_Method": "Fractional Logit GLM (HC1)",
        },
        {
            "Metric": "Complaints Per 1k Policies",
            "Control": f"{rate_comp_c:.2f}",
            "Treatment": f"{rate_comp_t:.2f}",
            "ATE": f"{ate_comp:+.2f}",
            "CI_95": "N/A (Poisson)",
            "p_value": p_val_comp,
            "Significant_5pct": p_val_comp < 0.05,
            "Test_Method": "Poisson GLM Regression",
        },
    ]

    res_df = pd.DataFrame(results)
    csv_path = REPORTS_DIR / "effect_sizes.csv"
    res_df.to_csv(csv_path, index=False)
    logger.info(f"Primary analysis effect sizes saved to {csv_path}")

    # 6. Conversion Funnel Chart Generation
    qc_ctrl = ctrl_sess["quote_completed"].sum() / n_ctrl
    qc_trt = trt_sess["quote_completed"].sum() / n_trt

    stages = ["1. Visitor Sessions", "2. Quote Completed", "3. Policy Purchase"]
    ctrl_funnel = [100.0, qc_ctrl * 100, p_ctrl * 100]
    trt_funnel = [100.0, qc_trt * 100, p_trt * 100]

    x = np.arange(len(stages))
    width = 0.35

    plt.figure(figsize=(9, 5.5))
    plt.bar(x - width / 2, ctrl_funnel, width, label="Control", color="#2b5c8f")
    plt.bar(x + width / 2, trt_funnel, width, label="Treatment", color="#d95f02")

    plt.ylabel("Conversion Rate (%)", fontsize=11, fontweight="bold")
    plt.title("Visitor Conversion Funnel Comparison by Experimental Arm", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(x, stages, fontsize=10)
    plt.ylim(0, 115)
    plt.grid(axis="y", linestyle=":", alpha=0.7)

    for i in range(len(stages)):
        plt.text(i - width / 2, ctrl_funnel[i] + 2, f"{ctrl_funnel[i]:.1f}%", ha="center", fontsize=9, fontweight="bold")
        plt.text(i + width / 2, trt_funnel[i] + 2, f"{trt_funnel[i]:.1f}%", ha="center", fontsize=9, fontweight="bold")

    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()

    funnel_path = REPORTS_DIR / "conversion_funnel.png"
    plt.savefig(funnel_path, dpi=300)
    plt.close()
    logger.info(f"Conversion funnel chart saved to {funnel_path}")

    return res_df, str(csv_path), str(funnel_path)


def main() -> None:
    """Executes primary analysis engine."""
    run_primary_analysis()


if __name__ == "__main__":
    main()
