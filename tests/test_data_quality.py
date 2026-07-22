"""Unit Tests for Data Quality and Pipeline Output Validation."""

import polars as pl
import pytest
from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR


def test_processed_files_exist():
    """Verifies that processed parquet files exist after simulation."""
    sess_file = PROCESSED_DATA_DIR / "session_data.parquet"
    assert sess_file.exists(), "session_data.parquet must exist after pipeline run"
    df = pl.read_parquet(sess_file)
    assert len(df) > 0, "Session dataset should not be empty"
    assert "converted" in df.columns, "Session dataset must contain 'converted'"
    assert "quoted_premium" in df.columns, "Session dataset must contain 'quoted_premium'"


def test_session_data_columns():
    """Verifies required columns and types in session data."""
    df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet")
    required_cols = {"session_id", "arm", "region", "device", "vulnerability_flag", "converted", "quoted_premium"}
    assert required_cols.issubset(set(df.columns)), f"Missing columns: {required_cols - set(df.columns)}"
    assert df["arm"].dtype == pl.String or df["arm"].dtype == pl.Utf8
    assert df["converted"].dtype in (pl.Int32, pl.Int64), "converted must be integer"


def test_session_data_ranges():
    """Verifies value ranges for critical session columns."""
    df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet")
    assert df["converted"].is_between(0, 1).all(), "converted must be binary (0 or 1)"
    assert df["vulnerability_flag"].is_between(0, 1).all(), "vulnerability_flag must be binary"
    assert (df["quoted_premium"] >= 0).all(), "quoted_premium must be non-negative"


def test_claims_data_integrity():
    """Verifies claims data structure and values."""
    claims_file = PROCESSED_DATA_DIR / "claims_data.parquet"
    assert claims_file.exists(), "claims_data.parquet must exist"
    df = pl.read_parquet(claims_file)
    assert len(df) > 0, "Claims dataset should not be empty"
    assert "claims_flag" in df.columns
    assert "claim_amount" in df.columns
    assert df["claim_amount"].is_between(0.0, 1_000_000).all(), "claim_amount out of plausible range"


def test_complaints_data_integrity():
    """Verifies complaints data structure."""
    comp_file = PROCESSED_DATA_DIR / "complaints_data.parquet"
    assert comp_file.exists(), "complaints_data.parquet must exist"
    df = pl.read_parquet(comp_file)
    assert "complaint_flag" in df.columns
    assert "arm" in df.columns
    assert df["complaint_flag"].is_between(0, 1).all(), "complaint_flag must be binary"


def test_arm_balance():
    """Verifies treatment/control split is approximately 50:50."""
    df = pl.read_parquet(PROCESSED_DATA_DIR / "session_data.parquet")
    counts = df.group_by("arm").len()
    count_map = dict(counts.iter_rows())
    total = sum(count_map.values())
    treated_pct = count_map.get("treatment", 0) / total
    control_pct = count_map.get("control", 0) / total
    assert abs(treated_pct - 0.5) < 0.05, f"Treatment split {treated_pct:.3f} deviates from 50%"
    assert abs(control_pct - 0.5) < 0.05, f"Control split {control_pct:.3f} deviates from 50%"
