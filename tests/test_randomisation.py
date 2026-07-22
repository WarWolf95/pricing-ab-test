"""Unit Tests for Randomisation Balance Checks."""

import numpy as np
import pytest
from src.randomisation_check import compute_smd


def test_compute_smd_identical():
    """Tests SMD calculation when arrays have identical distributions."""
    arr1 = np.ones(100)
    arr2 = np.ones(100)
    smd = compute_smd(arr1, arr2)
    assert smd == 0.0, f"Expected SMD 0.0, got {smd}"


def test_compute_smd_different():
    """Tests SMD calculation for different distributions."""
    arr1 = np.zeros(1000)
    arr2 = np.ones(1000)
    smd = compute_smd(arr1, arr2)
    assert smd > 0.5, f"Expected SMD > 0.5 for separate arrays, got {smd}"
