"""Experimental Data Simulator Module.

Generates 124,000 stratified block-randomised visitor sessions, quotes, purchases,
claims, and complaints data calibrated to FCA GI Value Measures and ONS distributions.
Outputs datasets to data/processed/ in Parquet format.
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import polars as pl

from src.config import (
    AVG_CLAIM_COST,
    CLAIMS_ACCEPTANCE_RATE,
    CLAIMS_FREQUENCY,
    CONTROL_CONVERSION_RATE,
    CONTROL_MEAN_PREMIUM,
    CONTROL_SD_PREMIUM,
    DEVICE_TYPES,
    DEVICE_WEIGHTS,
    MDE_CONVERSION,
    PROCESSED_DATA_DIR,
    RANDOM_SEED,
    REGIONAL_WEIGHTS,
    TARGET_SAMPLE_PER_ARM,
    TOTAL_TARGET_SAMPLE,
    TREATMENT_PREMIUM_MULT,
    UK_REGIONS,
    VULNERABILITY_CATEGORIES,
    VULNERABILITY_RATE,
)
from src.utils import setup_logger

logger = setup_logger("simulate_experiment")


def generate_experimental_data(
    n_total: int = TOTAL_TARGET_SAMPLE,
    seed: int = RANDOM_SEED,
) -> Tuple[str, str, str]:
    """Generates synthetic experimental session, claims, and complaints datasets.

    Args:
        n_total: Total number of visitor sessions (split 50:50).
        seed: Random seed for reproducibility.

    Returns:
        Tuple[str, str, str]: Paths to session, claims, and complaints Parquet files.
    """
    logger.info(f"Simulating {n_total:,} experimental visitor sessions (Seed={seed})...")
    np.random.seed(seed)

    # 1. Stratified Block Randomisation (Region x Device)
    strata_list: List[Tuple[str, str]] = []
    strata_weights: List[float] = []

    for r in UK_REGIONS:
        for d in DEVICE_TYPES:
            strata_list.append((r, d))
            strata_weights.append(REGIONAL_WEIGHTS[r] * DEVICE_WEIGHTS[d])

    strata_weights = np.array(strata_weights)
    strata_weights = strata_weights / strata_weights.sum()

    # Assign strata to visitors
    chosen_strata_idx = np.random.choice(len(strata_list), size=n_total, p=strata_weights)
    regions = [strata_list[idx][0] for idx in chosen_strata_idx]
    devices = [strata_list[idx][1] for idx in chosen_strata_idx]

    # Stratified 50:50 Arm Assignment
    # Use Bernoulli(0.5) per visitor for genuine randomness within strata,
    # which naturally produces the minor imbalances seen in real experiments.
    arms = np.empty(n_total, dtype=object)
    for s_idx in range(len(strata_list)):
        mask = chosen_strata_idx == s_idx
        count = mask.sum()
        if count > 0:
            rng = np.random.RandomState(np.random.randint(0, 2**31))
            arms[mask] = np.where(rng.rand(count) < 0.5, "treatment", "control")

    # 2. Customer Attributes & Vulnerability Status
    # Vulnerability rate ~47%
    is_vulnerable = np.random.rand(n_total) < VULNERABILITY_RATE
    vuln_types = np.array(["None"] * n_total, dtype=object)

    categories = list(VULNERABILITY_CATEGORIES.keys())
    cat_weights = np.array(list(VULNERABILITY_CATEGORIES.values()))
    cat_weights = cat_weights / cat_weights.sum()

    vuln_count = is_vulnerable.sum()
    if vuln_count > 0:
        vuln_types[is_vulnerable] = np.random.choice(categories, size=vuln_count, p=cat_weights)

    # Demographic proxies (Age & Earnings)
    age_bands = np.random.choice(
        ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        size=n_total,
        p=[0.10, 0.22, 0.24, 0.20, 0.14, 0.10],
    )

    soc_codes = np.random.choice(
        ["1115", "2136", "2423", "3533", "4159", "8211"],
        size=n_total,
        p=[0.05, 0.15, 0.20, 0.15, 0.30, 0.15],
    )

    # 3. Funnel & Conversion Rates (Primary Estimand)
    # Quote Completion Rate ~88%
    quote_completed = np.random.rand(n_total) < 0.88

    # Base conversion probability
    p_conv = np.where(arms == "control", CONTROL_CONVERSION_RATE, CONTROL_CONVERSION_RATE + MDE_CONVERSION)

    # Slight device effect (Desktop converts higher than Mobile)
    device_adj = np.where(np.array(devices) == "Desktop", 0.01, np.where(np.array(devices) == "Mobile", -0.005, 0.0))
    p_conv = np.clip(p_conv + device_adj, 0.01, 0.99)

    converted = np.where(quote_completed, np.random.rand(n_total) < p_conv, False)

    # 4. Premium Generation (Log-Normal Distribution)
    # Control Mean £587, sd £230 -> log-normal mu and sigma
    sd = CONTROL_SD_PREMIUM
    mean = CONTROL_MEAN_PREMIUM
    sigma2 = np.log(1 + (sd / mean) ** 2)
    mu = np.log(mean) - 0.5 * sigma2
    sigma = np.sqrt(sigma2)

    base_premiums = np.random.lognormal(mean=mu, sigma=sigma, size=n_total)
    quoted_premiums = np.where(arms == "treatment", base_premiums * TREATMENT_PREMIUM_MULT, base_premiums)
    quoted_premiums = np.round(quoted_premiums, 2)

    # 5. Session DataFrame Construction
    session_ids = [f"SESS-{i:07d}" for i in range(1, n_total + 1)]
    strata_ids = [f"{r}_{d}" for r, d in zip(regions, devices)]

    df_sessions = pd.DataFrame({
        "session_id": session_ids,
        "arm": arms,
        "strata_id": strata_ids,
        "region": regions,
        "device": devices,
        "vulnerability_flag": is_vulnerable.astype(int),
        "vulnerability_type": vuln_types,
        "age_band": age_bands,
        "soc_code": soc_codes,
        "quote_completed": quote_completed.astype(int),
        "converted": converted.astype(int),
        "quoted_premium": quoted_premiums,
    })

    # 6. Claims Simulation for Converted Policies
    policyholders = df_sessions[df_sessions["converted"] == 1].copy()
    n_policies = len(policyholders)

    claims_flag = np.random.rand(n_policies) < CLAIMS_FREQUENCY
    claim_accepted = np.where(claims_flag, np.random.rand(n_policies) < CLAIMS_ACCEPTANCE_RATE, False)

    # Exponential claim size with mean AVG_CLAIM_COST
    claim_amounts = np.where(
        claim_accepted,
        np.round(np.random.exponential(scale=AVG_CLAIM_COST, size=n_policies), 2),
        0.0,
    )

    df_claims = pd.DataFrame({
        "session_id": policyholders["session_id"].values,
        "arm": policyholders["arm"].values,
        "claims_flag": claims_flag.astype(int),
        "claim_accepted": claim_accepted.astype(int),
        "claim_amount": claim_amounts,
    })

    # 7. Complaints Simulation
    # Target complaints per 1k ~ 11.2 (Control), slightly higher or neutral in Treatment
    p_complaint_control = 11.2 / 1000.0
    p_complaint_treatment = 11.5 / 1000.0

    p_complaint = np.where(policyholders["arm"] == "control", p_complaint_control, p_complaint_treatment)
    complaint_flag = np.random.rand(n_policies) < p_complaint

    complaint_categories = np.random.choice(
        ["Pricing Fairness", "Claim Dispute", "Customer Service", "Policy Terms"],
        size=n_policies,
        p=[0.45, 0.25, 0.20, 0.10],
    )
    complaint_categories = np.where(complaint_flag, complaint_categories, "None")

    df_complaints = pd.DataFrame({
        "session_id": policyholders["session_id"].values,
        "arm": policyholders["arm"].values,
        "complaint_flag": complaint_flag.astype(int),
        "complaint_category": complaint_categories,
    })

    # Save to Parquet via Polars
    session_file = PROCESSED_DATA_DIR / "session_data.parquet"
    claims_file = PROCESSED_DATA_DIR / "claims_data.parquet"
    complaints_file = PROCESSED_DATA_DIR / "complaints_data.parquet"

    pl.from_pandas(df_sessions).write_parquet(session_file)
    pl.from_pandas(df_claims).write_parquet(claims_file)
    pl.from_pandas(df_complaints).write_parquet(complaints_file)

    logger.info(f"Simulated experimental datasets saved successfully to {PROCESSED_DATA_DIR}")
    return str(session_file), str(claims_file), str(complaints_file)


def main() -> None:
    """Executes experiment dataset generation."""
    generate_experimental_data()


if __name__ == "__main__":
    main()
