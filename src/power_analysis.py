"""Pre-Experiment Power Analysis and Minimum Detectable Effect (MDE) Module.

Calculates required sample size per arm, total trial duration, power sensitivity,
and outputs power analysis results to reports/power_analysis.csv.
"""

from typing import Dict, Tuple

import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, samplesize_proportions_2indep_onetail

from src.config import (
    ALLOCATION_RATIO,
    ALPHA,
    CONTROL_CONVERSION_RATE,
    MDE_CONVERSION,
    POWER,
    REPORTS_DIR,
    TARGET_SAMPLE_PER_ARM,
    TOTAL_TARGET_SAMPLE,
    TREATMENT_CONVERSION_RATE,
    WEEKLY_TRAFFIC,
)
from src.utils import setup_logger

logger = setup_logger("power_analysis")


def calculate_sample_size(
    p1: float = CONTROL_CONVERSION_RATE,
    p2: float = TREATMENT_CONVERSION_RATE,
    alpha: float = ALPHA,
    power: float = POWER,
) -> int:
    """Calculates required sample size per arm for a two-sample proportion z-test.

    Args:
        p1: Baseline conversion rate (Control).
        p2: Expected conversion rate (Treatment).
        alpha: Significance level (two-sided).
        power: Statistical power (1 - beta).

    Returns:
        int: Required sample size per arm rounded up.
    """
    effect_size = proportion_effectsize(p1, p2)
    solver = NormalIndPower()
    n_per_arm = solver.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative="two-sided",
    )
    return int(round(n_per_arm))


def calculate_mde(
    n_per_arm: int = TARGET_SAMPLE_PER_ARM,
    p1: float = CONTROL_CONVERSION_RATE,
    alpha: float = ALPHA,
    power: float = POWER,
) -> float:
    """Calculates Minimum Detectable Effect (MDE) in proportion lift for a fixed sample size.

    Args:
        n_per_arm: Available sample size per arm.
        p1: Baseline conversion rate.
        alpha: Significance level.
        power: Target power.

    Returns:
        float: Minimum detectable absolute proportion lift.
    """
    solver = NormalIndPower()
    target_effect_size = solver.solve_power(
        nobs1=n_per_arm,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative="two-sided",
    )
    # Estimate p2 from h = 2 * (arcsin(sqrt(p2)) - arcsin(sqrt(p1)))
    # For small p, effect_size h ≈ (p2 - p1) / sqrt(p1 * (1 - p1))
    import numpy as np

    p2_approx = p1 + target_effect_size * np.sqrt(p1 * (1.0 - p1))
    return float(p2_approx - p1)


def generate_power_report() -> Tuple[pd.DataFrame, str]:
    """Generates comprehensive power analysis parameter table and exports to CSV.

    Returns:
        Tuple[pd.DataFrame, str]: Result dataframe and absolute file path.
    """
    logger.info("Executing Pre-Experiment Power Analysis...")

    req_n_per_arm = calculate_sample_size()
    total_req_n = req_n_per_arm * 2
    estimated_weeks = total_req_n / WEEKLY_TRAFFIC
    mde_obs = calculate_mde(TARGET_SAMPLE_PER_ARM)

    metrics = [
        {"Parameter": "Significance Level (Alpha)", "Value": f"{ALPHA:.2f}", "Notes": "Two-sided hypothesis test"},
        {"Parameter": "Statistical Power (1 - Beta)", "Value": f"{POWER:.2f}", "Notes": "80% standard target"},
        {"Parameter": "Control Base Conversion Rate (p1)", "Value": f"{CONTROL_CONVERSION_RATE * 100:.2f}%", "Notes": "Calibrated from FCA GI Pricing data"},
        {"Parameter": "Treatment Target Conversion Rate (p2)", "Value": f"{TREATMENT_CONVERSION_RATE * 100:.2f}%", "Notes": "0.5 pp lift target"},
        {"Parameter": "Minimum Detectable Effect (MDE)", "Value": f"{MDE_CONVERSION * 100:.2f} pp", "Notes": "Absolute lift target"},
        {"Parameter": "Calculated Required n Per Arm", "Value": f"{req_n_per_arm:,}", "Notes": "Statsmodels NormalIndPower"},
        {"Parameter": "Total Required Sample Size", "Value": f"{total_req_n:,}", "Notes": "50:50 allocation split"},
        {"Parameter": "Actual Planned Sample Size", "Value": f"{TOTAL_TARGET_SAMPLE:,}", "Notes": "62k per arm"},
        {"Parameter": "Estimated Trial Duration (Weeks)", "Value": f"{estimated_weeks:.1f} weeks", "Notes": "Based on 10,000 visitors/week"},
    ]

    df = pd.DataFrame(metrics)
    file_path = REPORTS_DIR / "power_analysis.csv"
    df.to_csv(file_path, index=False)
    logger.info(f"Power analysis report saved to {file_path}")
    return df, str(file_path)


def main() -> None:
    """Executes power analysis script."""
    generate_power_report()


if __name__ == "__main__":
    main()
