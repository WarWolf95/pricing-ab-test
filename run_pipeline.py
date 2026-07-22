"""Root Master Orchestration Script for Pricing A/B Test Pipeline.

Executes steps 1 to 10 sequentially:
1. Ingest FCA Benchmark Data
2. Ingest ONS Demographic Data
3. Pre-Experiment Power Analysis
4. Calibrated Experimental Simulation
5. Randomisation & Covariate Balance Checks
6. Primary Hypothesis Tests & Effect Sizes
7. Subgroup CATE Analysis & FDR Control
8. Consumer Duty Compliance Audit
9. Sensitivity & Robustness Analysis
10. Programmatic Stakeholder Excel Dashboard Build
"""

import sys
from src.build_excel_dashboard import build_excel_workbook
from src.consumer_duty_checks import run_consumer_duty_checks
from src.fetch_fca_data import main as fetch_fca_main
from src.fetch_ons_data import main as fetch_ons_main
from src.power_analysis import generate_power_report
from src.primary_analysis import run_primary_analysis
from src.randomisation_check import run_randomisation_check
from src.sensitivity_analysis import run_sensitivity_analysis
from src.simulate_experiment import generate_experimental_data
from src.subgroup_analysis import run_subgroup_analysis
from src.utils import setup_logger

logger = setup_logger("run_pipeline")


STEPS = [
    ("Step 1/10", "Ingesting FCA GI Value Measures & Pricing Practices Data", fetch_fca_main),
    ("Step 2/10", "Ingesting ONS Regional Population & ASHE Earnings Data", fetch_ons_main),
    ("Step 3/10", "Executing Pre-Experiment Power Analysis", generate_power_report),
    ("Step 4/10", "Generating 124,000 Stratified Experimental Visitor Sessions", generate_experimental_data),
    ("Step 5/10", "Executing Covariate Balance Checks & Love Plot Generation", run_randomisation_check),
    ("Step 6/10", "Running Primary Hypothesis Tests & Conversion Funnel Engine", run_primary_analysis),
    ("Step 7/10", "Evaluating Heterogeneous Treatment Effects & BH FDR Adjustment", run_subgroup_analysis),
    ("Step 8/10", "Performing FCA Consumer Duty Regulatory Compliance Audit", run_consumer_duty_checks),
    ("Step 9/10", "Running ITT/PP, Bootstrap CIs, and E-Value Robustness Bounds", run_sensitivity_analysis),
    ("Step 10/10", "Building Programmatic Stakeholder Excel Dashboard Workbook", build_excel_workbook),
]


def run_full_pipeline() -> None:
    """Executes the 10-step pricing A/B test pipeline end-to-end."""
    logger.info("=====================================================================")
    logger.info("STARTING UK MOTOR INSURANCE PRICING A/B TEST PIPELINE EXECUTION")
    logger.info("=====================================================================")

    failed_steps = []
    for step_label, description, func in STEPS:
        logger.info("[%s] %s...", step_label, description)
        try:
            func()
            logger.info("[%s] %s — COMPLETED", step_label, description)
        except Exception as exc:
            logger.error("[%s] %s — FAILED: %s", step_label, description, exc)
            failed_steps.append(step_label)

    logger.info("=====================================================================")
    if failed_steps:
        logger.error(
            "PIPELINE COMPLETED WITH ERRORS in steps: %s. Check logs above for details.",
            ", ".join(failed_steps),
        )
    else:
        logger.info("SUCCESS: UK MOTOR INSURANCE PRICING A/B TEST PIPELINE COMPLETED!")
    logger.info("=====================================================================")


if __name__ == "__main__":
    run_full_pipeline()
