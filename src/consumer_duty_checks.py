"""FCA Consumer Duty Compliance and Governance Audit Engine.

Evaluates vulnerable customer outcome disparities, portfolio fair value ratios,
and complaint rates against FCA Consumer Duty regulations (PS22/9, FG22/5).
Generates reports/consumer_duty_compliance.csv.
"""

from typing import Tuple

import numpy as np
import pandas as pd
import polars as pl

from src.config import (
    FCA_LOSS_RATIO_BENCHMARK,
    MAX_COMPLAINTS_PER_1K,
    MAX_VULNERABLE_CONVERSION_DISPARITY,
    MAX_VULNERABLE_LOSS_RATIO_DISPARITY,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
)
from src.utils import setup_logger

logger = setup_logger("consumer_duty_checks")


def run_consumer_duty_checks() -> Tuple[pd.DataFrame, str]:
    """Executes regulatory Consumer Duty compliance checks and exports findings table.

    Returns:
        Tuple[pd.DataFrame, str]: Compliance dataframe and output CSV path.
    """
    logger.info("Running FCA Consumer Duty Compliance Audit...")

    sessions_df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet").to_pandas()
    claims_df = pl.read_parquet(PROCESSED_DATA_DIR / "claims_data.parquet").to_pandas()
    complaints_df = pl.read_parquet(PROCESSED_DATA_DIR / "complaints_data.parquet").to_pandas()

    checks = []

    # 1. Vulnerable vs Non-Vulnerable Conversion Disparity Check
    vuln_df = sessions_df[sessions_df["vulnerability_flag"] == 1]
    non_vuln_df = sessions_df[sessions_df["vulnerability_flag"] == 0]

    conv_vuln_trt = vuln_df[vuln_df["arm"] == "treatment"]["converted"].mean()
    conv_non_vuln_trt = non_vuln_df[non_vuln_df["arm"] == "treatment"]["converted"].mean()

    rel_conv_disparity = np.abs(conv_vuln_trt - conv_non_vuln_trt) / conv_non_vuln_trt
    pass_conv_disp = rel_conv_disparity <= MAX_VULNERABLE_CONVERSION_DISPARITY

    checks.append({
        "Check_Domain": "Consumer Duty Outcomes (Conversion)",
        "Metric_Name": "Vulnerable Conversion Disparity",
        "Observed_Value": f"{rel_conv_disparity * 100:.2f}% relative gap",
        "Regulatory_Threshold": f"<= {MAX_VULNERABLE_CONVERSION_DISPARITY * 100:.1f}% relative gap",
        "Status": "PASS" if pass_conv_disp else "FAIL",
        "Regulatory_Reference": "FCA PS22/9 & FG22/5 (Cross-cutting Outcome)",
    })

    # 2. Vulnerable vs Non-Vulnerable Loss Ratio Disparity
    policy_df = sessions_df[sessions_df["converted"] == 1].merge(claims_df, on=["session_id", "arm"], how="left")
    policy_df["claim_amount"] = policy_df["claim_amount"].fillna(0.0)

    vuln_pol_trt = policy_df[(policy_df["vulnerability_flag"] == 1) & (policy_df["arm"] == "treatment")]
    non_vuln_pol_trt = policy_df[(policy_df["vulnerability_flag"] == 0) & (policy_df["arm"] == "treatment")]

    lr_vuln_trt = vuln_pol_trt["claim_amount"].sum() / vuln_pol_trt["quoted_premium"].sum() if len(vuln_pol_trt) > 0 else 0.0
    lr_non_vuln_trt = non_vuln_pol_trt["claim_amount"].sum() / non_vuln_pol_trt["quoted_premium"].sum() if len(non_vuln_pol_trt) > 0 else 0.0

    rel_lr_disparity = np.abs(lr_vuln_trt - lr_non_vuln_trt) / lr_non_vuln_trt if lr_non_vuln_trt > 0 else 0.0
    pass_lr_disp = rel_lr_disparity <= MAX_VULNERABLE_LOSS_RATIO_DISPARITY

    checks.append({
        "Check_Domain": "Consumer Duty Outcomes (Loss Ratio)",
        "Metric_Name": "Vulnerable Loss Ratio Disparity",
        "Observed_Value": f"{rel_lr_disparity * 100:.2f}% relative gap",
        "Regulatory_Threshold": f"<= {MAX_VULNERABLE_LOSS_RATIO_DISPARITY * 100:.1f}% relative gap",
        "Status": "PASS" if pass_lr_disp else "FAIL",
        "Regulatory_Reference": "FCA PS22/9 & FG22/5 (Fair Value Rule)",
    })

    # 3. Portfolio Fair Value Assessment (Loss Ratio vs Benchmark)
    trt_pol = policy_df[policy_df["arm"] == "treatment"]
    overall_trt_lr = trt_pol["claim_amount"].sum() / trt_pol["quoted_premium"].sum()
    pass_fair_value = overall_trt_lr >= (FCA_LOSS_RATIO_BENCHMARK * 0.90)  # Must be within 90% of benchmark

    checks.append({
        "Check_Domain": "FCA Fair Value",
        "Metric_Name": "Portfolio Loss Ratio vs FCA GI Benchmark",
        "Observed_Value": f"{overall_trt_lr * 100:.2f}% (Benchmark: {FCA_LOSS_RATIO_BENCHMARK * 100:.1f}%)",
        "Regulatory_Threshold": f">= {FCA_LOSS_RATIO_BENCHMARK * 0.90 * 100:.1f}% (FCA Motor Benchmark)",
        "Status": "PASS" if pass_fair_value else "FAIL",
        "Regulatory_Reference": "FCA GI Value Measures 2024 / PROD 4",
    })

    # 4. Complaints Rate SLA Check
    comp_merged = sessions_df[sessions_df["converted"] == 1].merge(complaints_df, on=["session_id", "arm"], how="left")
    comp_merged["complaint_flag"] = comp_merged["complaint_flag"].fillna(0)
    trt_comp = comp_merged[comp_merged["arm"] == "treatment"]["complaint_flag"]
    trt_comp_rate_1k = (trt_comp.sum() / len(trt_comp)) * 1000.0

    pass_comp = trt_comp_rate_1k <= MAX_COMPLAINTS_PER_1K

    checks.append({
        "Check_Domain": "Consumer Duty Protection",
        "Metric_Name": "Complaints Per 1,000 Policies",
        "Observed_Value": f"{trt_comp_rate_1k:.2f} per 1k",
        "Regulatory_Threshold": f"<= {MAX_COMPLAINTS_PER_1K:.1f} per 1k",
        "Status": "PASS" if pass_comp else "FAIL",
        "Regulatory_Reference": "DISP 1.10 / Internal Risk Governance",
    })

    res_df = pd.DataFrame(checks)
    csv_path = REPORTS_DIR / "consumer_duty_compliance.csv"
    res_df.to_csv(csv_path, index=False)
    logger.info(f"Consumer Duty compliance audit table saved to {csv_path}")

    return res_df, str(csv_path)


def main() -> None:
    """Executes Consumer Duty checks."""
    run_consumer_duty_checks()


if __name__ == "__main__":
    main()
