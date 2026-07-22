"""Unit Tests for Analysis Calculations and Statistical Tests."""

import numpy as np
import pytest
from statsmodels.stats.proportion import proportions_ztest


def test_proportions_ztest_significance():
    """Tests two-sample z-test logic for proportions."""
    count = [5580, 5270]  # 9.0% vs 8.5%
    nobs = [62000, 62000]
    z_stat, p_val = proportions_ztest(count, nobs)
    assert p_val < 0.05, f"Expected significant p-value for 9.0% vs 8.5% at N=62k, got {p_val}"
