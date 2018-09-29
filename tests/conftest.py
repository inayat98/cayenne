"""
    Common configuration for all the tests
"""

import numpy as np
import pytest


@pytest.fixture
def setup_basic():
    V_r = np.array([[1, 0, 0], [0, 1, 0]])
    V_p = np.array([[0, 1, 0], [0, 0, 1]])
    X0 = np.array([100, 0, 0])
    k = np.array([1.0, 1.0])
    return V_r, V_p, X0, k


@pytest.fixture
def setup_large():
    V_r = np.array([[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1]])
    V_p = np.array([[0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1], [0, 0, 0, 0, 0]])
    X0 = np.array([10, 0, 0, 0, 0])
    k = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    return V_r, V_p, X0, k

@pytest.fixture
def setup_system():
    k_det = np.array([3.0])
    volume = 7.0
    return k_det, volume
