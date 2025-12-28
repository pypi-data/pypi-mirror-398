"""
Critical values and lambda bar parameters for the Carrion-i-Silvestre and Kim (2019) tests.

This module contains:
- Lambda bar (local-to-unity parameter) tables for different model specifications
- Critical values for robust CI, joint CI/CB, and joint CI/CT tests
- Tuning parameters for Dmax tests

All values are from the original paper and supplementary materials.
"""

import numpy as np
from typing import Dict, Tuple, Optional, Union

# =============================================================================
# Lambda Bar Tables
# =============================================================================
# Format: (m, Model, px) -> lambda_bar
# m = number of breaks (0, 1, 2)
# Model = 1 (mean shifts) or 2 (linear trend with intercept shifts)
# px = number of stochastic regressors (1-5)

LAMBDA_BAR_TABLES = {
    # m=0 (no breaks)
    (0, 1, 1): 9.1,
    (0, 1, 2): 10.8,
    (0, 1, 3): 12.4,
    (0, 1, 4): 13.9,
    (0, 1, 5): 15.5,
    (0, 2, 1): 13.3,
    (0, 2, 2): 14.6,
    (0, 2, 3): 16.0,
    (0, 2, 4): 17.4,
    (0, 2, 5): 19.1,
    # m=1 (one break)
    (1, 1, 1): 11.4,
    (1, 1, 2): 12.9,
    (1, 1, 3): 14.4,
    (1, 1, 4): 15.9,
    (1, 1, 5): 17.4,
    (1, 2, 1): 14.9,
    (1, 2, 2): 16.3,
    (1, 2, 3): 17.6,
    (1, 2, 4): 19.1,
    (1, 2, 5): 20.6,
    # m=2 (two breaks)
    (2, 1, 1): 13.8,
    (2, 1, 2): 15.2,
    (2, 1, 3): 16.6,
    (2, 1, 4): 18.0,
    (2, 1, 5): 19.3,
    (2, 2, 1): 16.9,
    (2, 2, 2): 18.1,
    (2, 2, 3): 19.5,
    (2, 2, 4): 20.9,
    (2, 2, 5): 22.7,
}

# =============================================================================
# Critical Values for Tests
# =============================================================================
# Asymptotic critical values at 1%, 5%, and 10% significance levels
# Source: Supplementary Appendix I of Carrion-i-Silvestre and Kim (2019)

# Format: (test_type, m, Model, px) -> (cv_10, cv_5, cv_1)
# test_type: 'robust_ci', 'joint_cb', 'joint_ct', 'dmax_cb', 'dmax_ct'

CRITICAL_VALUES = {
    # =========================================================================
    # Model I (mean shifts only) - Robust CI Test (Q_r)
    # =========================================================================
    # m=0 (no breaks)
    ('robust_ci', 0, 1, 1): (1.07, 1.68, 3.25),
    ('robust_ci', 0, 1, 2): (1.08, 1.69, 3.31),
    ('robust_ci', 0, 1, 3): (1.11, 1.72, 3.36),
    ('robust_ci', 0, 1, 4): (1.12, 1.74, 3.38),
    ('robust_ci', 0, 1, 5): (1.14, 1.75, 3.41),
    # m=1 (one break)
    ('robust_ci', 1, 1, 1): (1.12, 1.72, 3.34),
    ('robust_ci', 1, 1, 2): (1.14, 1.76, 3.42),
    ('robust_ci', 1, 1, 3): (1.17, 1.80, 3.48),
    ('robust_ci', 1, 1, 4): (1.19, 1.83, 3.55),
    ('robust_ci', 1, 1, 5): (1.21, 1.86, 3.60),
    # m=2 (two breaks)
    ('robust_ci', 2, 1, 1): (1.14, 1.73, 3.36),
    ('robust_ci', 2, 1, 2): (1.16, 1.78, 3.45),
    ('robust_ci', 2, 1, 3): (1.19, 1.83, 3.51),
    ('robust_ci', 2, 1, 4): (1.22, 1.86, 3.58),
    ('robust_ci', 2, 1, 5): (1.24, 1.89, 3.65),
    
    # =========================================================================
    # Model II (linear trend with intercept shifts) - Robust CI Test (Q_r)
    # =========================================================================
    # m=0 (no breaks)
    ('robust_ci', 0, 2, 1): (1.17, 1.77, 3.39),
    ('robust_ci', 0, 2, 2): (1.22, 1.83, 3.49),
    ('robust_ci', 0, 2, 3): (1.25, 1.88, 3.57),
    ('robust_ci', 0, 2, 4): (1.28, 1.92, 3.64),
    ('robust_ci', 0, 2, 5): (1.31, 1.96, 3.70),
    # m=1 (one break)
    ('robust_ci', 1, 2, 1): (1.19, 1.79, 3.44),
    ('robust_ci', 1, 2, 2): (1.24, 1.86, 3.54),
    ('robust_ci', 1, 2, 3): (1.28, 1.91, 3.62),
    ('robust_ci', 1, 2, 4): (1.31, 1.96, 3.70),
    ('robust_ci', 1, 2, 5): (1.34, 2.00, 3.77),
    # m=2 (two breaks)
    ('robust_ci', 2, 2, 1): (1.15, 1.73, 3.35),
    ('robust_ci', 2, 2, 2): (1.19, 1.80, 3.46),
    ('robust_ci', 2, 2, 3): (1.23, 1.86, 3.56),
    ('robust_ci', 2, 2, 4): (1.27, 1.91, 3.64),
    ('robust_ci', 2, 2, 5): (1.30, 1.95, 3.71),
    
    # =========================================================================
    # Model I - Joint CI/CB Test (Q_cb)
    # =========================================================================
    # m=0
    ('joint_cb', 0, 1, 1): (1.07, 1.68, 3.25),
    ('joint_cb', 0, 1, 2): (1.08, 1.69, 3.31),
    ('joint_cb', 0, 1, 3): (1.11, 1.72, 3.36),
    ('joint_cb', 0, 1, 4): (1.12, 1.74, 3.38),
    ('joint_cb', 0, 1, 5): (1.14, 1.75, 3.41),
    # m=1
    ('joint_cb', 1, 1, 1): (6.93, 11.27, 19.51),
    ('joint_cb', 1, 1, 2): (7.37, 12.13, 20.88),
    ('joint_cb', 1, 1, 3): (7.77, 12.93, 22.09),
    ('joint_cb', 1, 1, 4): (8.15, 13.67, 23.41),
    ('joint_cb', 1, 1, 5): (8.48, 14.35, 24.47),
    # m=2
    ('joint_cb', 2, 1, 1): (12.12, 18.96, 31.93),
    ('joint_cb', 2, 1, 2): (12.98, 20.42, 34.21),
    ('joint_cb', 2, 1, 3): (13.79, 21.79, 36.31),
    ('joint_cb', 2, 1, 4): (14.54, 23.04, 38.35),
    ('joint_cb', 2, 1, 5): (15.28, 24.23, 40.26),
    
    # =========================================================================
    # Model II - Joint CI/CB Test (Q_cb)
    # =========================================================================
    # m=0
    ('joint_cb', 0, 2, 1): (1.17, 1.77, 3.39),
    ('joint_cb', 0, 2, 2): (1.22, 1.83, 3.49),
    ('joint_cb', 0, 2, 3): (1.25, 1.88, 3.57),
    ('joint_cb', 0, 2, 4): (1.28, 1.92, 3.64),
    ('joint_cb', 0, 2, 5): (1.31, 1.96, 3.70),
    # m=1
    ('joint_cb', 1, 2, 1): (8.04, 13.07, 22.67),
    ('joint_cb', 1, 2, 2): (8.37, 13.55, 23.58),
    ('joint_cb', 1, 2, 3): (8.70, 14.02, 24.30),
    ('joint_cb', 1, 2, 4): (8.99, 14.44, 25.01),
    ('joint_cb', 1, 2, 5): (9.27, 14.84, 25.73),
    # m=2
    ('joint_cb', 2, 2, 1): (13.88, 22.02, 37.26),
    ('joint_cb', 2, 2, 2): (14.51, 22.93, 38.50),
    ('joint_cb', 2, 2, 3): (15.12, 23.78, 39.72),
    ('joint_cb', 2, 2, 4): (15.68, 24.57, 40.86),
    ('joint_cb', 2, 2, 5): (16.20, 25.31, 41.92),
    
    # =========================================================================
    # Model II - Joint CI/CT Test (Q_ct) [Not applicable for Model I]
    # =========================================================================
    # m=0
    ('joint_ct', 0, 2, 1): (4.48, 6.78, 11.44),
    ('joint_ct', 0, 2, 2): (4.55, 6.93, 11.70),
    ('joint_ct', 0, 2, 3): (4.66, 7.10, 12.00),
    ('joint_ct', 0, 2, 4): (4.77, 7.26, 12.27),
    ('joint_ct', 0, 2, 5): (4.87, 7.42, 12.54),
    # m=1
    ('joint_ct', 1, 2, 1): (11.00, 17.43, 29.74),
    ('joint_ct', 1, 2, 2): (11.49, 18.10, 30.74),
    ('joint_ct', 1, 2, 3): (11.93, 18.73, 31.70),
    ('joint_ct', 1, 2, 4): (12.35, 19.30, 32.58),
    ('joint_ct', 1, 2, 5): (12.73, 19.84, 33.40),
    # m=2
    ('joint_ct', 2, 2, 1): (16.80, 26.36, 44.42),
    ('joint_ct', 2, 2, 2): (17.57, 27.33, 45.70),
    ('joint_ct', 2, 2, 3): (18.27, 28.24, 46.94),
    ('joint_ct', 2, 2, 4): (18.92, 29.08, 48.06),
    ('joint_ct', 2, 2, 5): (19.53, 29.86, 49.12),
}

# =============================================================================
# Tuning Parameters for Dmax Tests
# =============================================================================
# Format: (Model, px) -> array of [a_m, b_m] for m=0,1,2

DMAX_CB_PARAMS = {
    # Model I
    (1, 1): np.array([
        [1.68, 4.06 - 1.68],   # m=0
        [11.27, 14.91 - 11.27], # m=1
        [18.96, 23.26 - 18.96], # m=2
    ]),
    (1, 2): np.array([
        [1.69, 4.07 - 1.69],
        [12.13, 15.97 - 12.13],
        [20.42, 24.92 - 20.42],
    ]),
    # Model II
    (2, 1): np.array([
        [1.77, 4.02 - 1.77],
        [13.07, 16.76 - 13.07],
        [22.02, 26.43 - 22.02],
    ]),
    (2, 2): np.array([
        [1.83, 4.10 - 1.83],
        [13.55, 17.38 - 13.55],
        [22.93, 27.31 - 22.93],
    ]),
}

DMAX_CT_PARAMS = {
    # Model I (cotrending not applicable)
    (1, 1): np.array([
        [0, 1],
        [0, 1],
        [0, 1],
    ]),
    (1, 2): np.array([
        [0, 1],
        [0, 1],
        [0, 1],
    ]),
    # Model II
    (2, 1): np.array([
        [6.78, 9.94 - 6.78],
        [17.43, 21.54 - 17.43],
        [26.36, 31.10 - 26.36],
    ]),
    (2, 2): np.array([
        [6.93, 10.00 - 6.93],
        [18.10, 22.11 - 18.10],
        [27.33, 31.81 - 27.33],
    ]),
}

# Dmax test critical values at 5% and 1%
DMAX_CRITICAL_VALUES = {
    # (test_type, Model, px) -> (cv_5, cv_1)
    ('dmax_cb', 1, 1): (0.39, 1.0),
    ('dmax_cb', 1, 2): (0.39, 1.0),
    ('dmax_cb', 2, 1): (0.39, 1.0),
    ('dmax_cb', 2, 2): (0.39, 1.0),
    ('dmax_ct', 2, 1): (0.32, 1.0),
    ('dmax_ct', 2, 2): (0.32, 1.0),
}


def get_lambda_bar(
    m: int,
    model: int,
    px: int
) -> float:
    """
    Get the lambda bar (local-to-unity) parameter.
    
    Parameters
    ----------
    m : int
        Number of structural breaks (0, 1, or 2).
    model : int
        Model specification:
        - 1: Mean shifts only
        - 2: Linear trend with intercept shifts
    px : int
        Number of stochastic regressors (1-5).
    
    Returns
    -------
    float
        Lambda bar value for the specified configuration.
    
    Raises
    ------
    ValueError
        If the combination of (m, model, px) is not available.
    
    Examples
    --------
    >>> from co_eco.critical_values import get_lambda_bar
    >>> get_lambda_bar(m=1, model=2, px=1)
    14.9
    """
    key = (m, model, px)
    if key not in LAMBDA_BAR_TABLES:
        raise ValueError(
            f"Lambda bar not available for m={m}, model={model}, px={px}. "
            f"Supported: m in {{0,1,2}}, model in {{1,2}}, px in {{1,2,3,4,5}}"
        )
    return LAMBDA_BAR_TABLES[key]


def get_critical_values(
    test_type: str,
    m: int,
    model: int,
    px: int,
    significance_level: float = 0.05
) -> float:
    """
    Get critical value for a specific test configuration.
    
    Parameters
    ----------
    test_type : str
        Type of test:
        - 'robust_ci': Robust cointegration test (Q_r)
        - 'joint_cb': Joint CI and cobreaking test (Q_cb)
        - 'joint_ct': Joint CI and cotrending test (Q_ct)
    m : int
        Number of structural breaks (0, 1, or 2).
    model : int
        Model specification (1 or 2).
    px : int
        Number of stochastic regressors (1-5).
    significance_level : float, default=0.05
        Significance level (0.01, 0.05, or 0.10).
    
    Returns
    -------
    float
        Critical value for the specified configuration.
    
    Raises
    ------
    ValueError
        If the combination is not available or significance level is invalid.
    
    Examples
    --------
    >>> from co_eco.critical_values import get_critical_values
    >>> cv = get_critical_values('robust_ci', m=1, model=2, px=1)
    >>> print(f"5% critical value: {cv}")
    5% critical value: 1.79
    """
    key = (test_type, m, model, px)
    if key not in CRITICAL_VALUES:
        raise ValueError(
            f"Critical values not available for test_type='{test_type}', "
            f"m={m}, model={model}, px={px}"
        )
    
    cv_10, cv_5, cv_1 = CRITICAL_VALUES[key]
    
    if significance_level == 0.10:
        return cv_10
    elif significance_level == 0.05:
        return cv_5
    elif significance_level == 0.01:
        return cv_1
    else:
        raise ValueError(
            f"Invalid significance level: {significance_level}. "
            f"Must be 0.01, 0.05, or 0.10."
        )


def get_all_critical_values(
    test_type: str,
    m: int,
    model: int,
    px: int
) -> Tuple[float, float, float]:
    """
    Get all critical values (10%, 5%, 1%) for a specific test configuration.
    
    Parameters
    ----------
    test_type : str
        Type of test ('robust_ci', 'joint_cb', 'joint_ct').
    m : int
        Number of structural breaks (0, 1, or 2).
    model : int
        Model specification (1 or 2).
    px : int
        Number of stochastic regressors (1-5).
    
    Returns
    -------
    tuple
        (cv_10, cv_5, cv_1) - Critical values at 10%, 5%, 1% levels.
    
    Examples
    --------
    >>> from co_eco.critical_values import get_all_critical_values
    >>> cv_10, cv_5, cv_1 = get_all_critical_values('joint_cb', 1, 2, 1)
    >>> print(f"10%: {cv_10}, 5%: {cv_5}, 1%: {cv_1}")
    10%: 8.04, 5%: 13.07, 1%: 22.67
    """
    key = (test_type, m, model, px)
    if key not in CRITICAL_VALUES:
        raise ValueError(
            f"Critical values not available for test_type='{test_type}', "
            f"m={m}, model={model}, px={px}"
        )
    return CRITICAL_VALUES[key]


def get_dmax_params(
    test_type: str,
    model: int,
    px: int
) -> np.ndarray:
    """
    Get Dmax test tuning parameters.
    
    Parameters
    ----------
    test_type : str
        'dmax_cb' for cobreaking or 'dmax_ct' for cotrending.
    model : int
        Model specification (1 or 2).
    px : int
        Number of stochastic regressors (1 or 2).
    
    Returns
    -------
    np.ndarray
        3x2 array with [a_m, b_m] for m=0,1,2.
    
    Examples
    --------
    >>> from co_eco.critical_values import get_dmax_params
    >>> params = get_dmax_params('dmax_cb', model=2, px=1)
    >>> a_1, b_1 = params[1, :]  # Parameters for m=1
    """
    key = (model, px)
    
    if test_type == 'dmax_cb':
        if key not in DMAX_CB_PARAMS:
            raise ValueError(f"Dmax CB params not available for model={model}, px={px}")
        return DMAX_CB_PARAMS[key]
    elif test_type == 'dmax_ct':
        if key not in DMAX_CT_PARAMS:
            raise ValueError(f"Dmax CT params not available for model={model}, px={px}")
        return DMAX_CT_PARAMS[key]
    else:
        raise ValueError(f"Invalid test_type: {test_type}")


def get_dmax_critical_value(
    test_type: str,
    model: int,
    px: int,
    significance_level: float = 0.05
) -> float:
    """
    Get critical value for Dmax test.
    
    Parameters
    ----------
    test_type : str
        'dmax_cb' or 'dmax_ct'.
    model : int
        Model specification (1 or 2).
    px : int
        Number of stochastic regressors.
    significance_level : float
        0.05 or 0.01.
    
    Returns
    -------
    float
        Critical value for the Dmax test.
    """
    key = (test_type, model, min(px, 2))
    if key not in DMAX_CRITICAL_VALUES:
        raise ValueError(f"Dmax critical value not available for {key}")
    
    cv_5, cv_1 = DMAX_CRITICAL_VALUES[key]
    
    if significance_level == 0.05:
        return cv_5
    elif significance_level == 0.01:
        return cv_1
    else:
        raise ValueError(f"Invalid significance level: {significance_level}")
