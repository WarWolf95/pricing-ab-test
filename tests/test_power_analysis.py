"""Unit Tests for Power Analysis Module."""

import pytest
from src.power_analysis import calculate_mde, calculate_sample_size


def test_calculate_sample_size_target():
    """Tests sample size calculation for baseline 8.5% and target 9.0%."""
    n_per_arm = calculate_sample_size(p1=0.085, p2=0.090, alpha=0.05, power=0.80)
    # Target sample size should be approximately 50,000-62,000 per arm
    assert 45000 <= n_per_arm <= 65000, f"Expected n_per_arm ~50k-62k, got {n_per_arm}"


def test_calculate_mde_range():
    """Tests MDE estimation for 62,000 visitors per arm."""
    mde = calculate_mde(n_per_arm=62000, p1=0.085, alpha=0.05, power=0.80)
    # MDE should be approx 0.005 (0.5 pp)
    assert 0.003 <= mde <= 0.007, f"Expected MDE ~0.005, got {mde}"
