"""Centralised Configuration Module for UK Motor Insurance Pricing A/B Test.

Defines all project constants, experimental parameters, regulatory thresholds,
FCA benchmark calibration parameters, and path references.
"""

from pathlib import Path
from typing import Dict, List

# --- Directory Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"
EXCEL_DIR = BASE_DIR / "excel"

# Ensure runtime directories exist
for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, EXCEL_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# --- Random Seed ---
RANDOM_SEED: int = 42

# --- Experimental Design Parameters ---
ALPHA: float = 0.05
POWER: float = 0.80
CONTROL_CONVERSION_RATE: float = 0.085  # 8.5% baseline
MDE_CONVERSION: float = 0.005          # 0.5 percentage point lift
TREATMENT_CONVERSION_RATE: float = CONTROL_CONVERSION_RATE + MDE_CONVERSION  # 9.0%
ALLOCATION_RATIO: float = 0.50
TARGET_SAMPLE_PER_ARM: int = 62000
TOTAL_TARGET_SAMPLE: int = TARGET_SAMPLE_PER_ARM * 2  # ~124,000
WEEKLY_TRAFFIC: int = 10000

# --- UK Motor Insurance Calibrated Parameters (Tier 1 Benchmarks) ---
CONTROL_MEAN_PREMIUM: float = 587.0    # £587 mean GWP
CONTROL_SD_PREMIUM: float = 230.0      # £230 standard deviation
TREATMENT_PREMIUM_MULT: float = 1.015  # Granular risk pricing slightly increases premium efficiency (+1.5%)
CLAIMS_FREQUENCY: float = 0.049        # 4.9% annual claim frequency (FCA GI Value Measures)
CLAIMS_ACCEPTANCE_RATE: float = 0.983  # 98.3% acceptance rate (FCA GI Value Measures)
AVG_CLAIM_COST: float = 2850.0         # £2,850 average claim severity
FCA_LOSS_RATIO_BENCHMARK: float = 0.544  # 54.4% portfolio loss ratio benchmark for Motor (FCA)

# --- Consumer Duty Governance & Regulatory Thresholds ---
VULNERABILITY_RATE: float = 0.47       # 47% per FCA Financial Lives Survey
VULNERABILITY_CATEGORIES: Dict[str, float] = {
    "Health": 0.32,
    "Resilience": 0.28,
    "Life Events": 0.22,
    "Capability": 0.18,
}
MAX_VULNERABLE_CONVERSION_DISPARITY: float = 0.05  # Max 5% relative conversion gap
MAX_VULNERABLE_LOSS_RATIO_DISPARITY: float = 0.05 # Max 5% relative loss ratio gap
MAX_COMPLAINTS_PER_1K: float = 15.0                # Internal SLA benchmark per 1,000 policies

# --- Stratification Factors ---
UK_REGIONS: List[str] = [
    "North East",
    "North West",
    "Yorkshire and the Humber",
    "East Midlands",
    "West Midlands",
    "East of England",
    "London",
    "South East",
    "South West",
    "Wales",
    "Scotland",
    "Northern Ireland",
]

REGIONAL_WEIGHTS: Dict[str, float] = {
    "North East": 0.04,
    "North West": 0.11,
    "Yorkshire and the Humber": 0.08,
    "East Midlands": 0.07,
    "West Midlands": 0.09,
    "East of England": 0.09,
    "London": 0.13,
    "South East": 0.14,
    "South West": 0.08,
    "Wales": 0.05,
    "Scotland": 0.08,
    "Northern Ireland": 0.04,
}

DEVICE_TYPES: List[str] = ["Desktop", "Mobile", "Tablet"]
DEVICE_WEIGHTS: Dict[str, float] = {"Desktop": 0.35, "Mobile": 0.55, "Tablet": 0.10}
