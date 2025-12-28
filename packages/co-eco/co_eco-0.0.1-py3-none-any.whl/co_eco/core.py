"""
Core test functions for the co-eco package.

This module implements the quasi-likelihood ratio tests for cointegration,
cobreaking, and cotrending proposed by Carrion-i-Silvestre and Kim (2019).

All functions are exact translations of the original MATLAB code to ensure
full compatibility and reproducibility.

Reference
---------
Carrion-i-Silvestre, J.L. and Kim, D. (2019). Quasi-likelihood ratio tests 
for cointegration, cobreaking, and cotrending. Econometric Reviews.
"""

import numpy as np
from numpy.linalg import solve, det, inv, cholesky
from typing import Tuple, Optional, Union, List
import warnings

from co_eco.utils import (
    long_run_variance,
    dols_reg_maker,
    create_step_dummies,
    compute_adjustment_factor,
    ols_detrend,
    quasi_difference_transform,
)
from co_eco.critical_values import (
    get_lambda_bar,
    get_critical_values,
    get_all_critical_values,
    get_dmax_params,
    get_dmax_critical_value,
)
from co_eco.results import CKTestResults, DmaxTestResults


def ck_test_known_breaks(
    y: np.ndarray,
    x: np.ndarray,
    model: int,
    break_dates: Optional[Union[List[int], np.ndarray]] = None,
    lambda_hat: Optional[float] = None,
    klags: int = 0,
    kleads: int = 0
) -> Tuple[float, float, float]:
    """
    Quasi-likelihood ratio tests with known break dates.
    
    Computes the robust CI test (Q_r), joint CI/CB test (Q_cb), and 
    joint CI/CT test (Q_ct) when break dates are known.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (T x 1).
    x : np.ndarray
        Stochastic regressors (T x px).
    model : int
        Model specification:
        - 1: Mean shifts only (no linear trend)
        - 2: Linear trend with intercept shifts
    break_dates : list or np.ndarray, optional
        Vector of break dates (indices). Use None or [] for no breaks.
    lambda_hat : float, optional
        Local-to-unity parameter. If None, uses optimal value from tables.
    klags : int, default=0
        Number of lags for DOLS correction (0 for exogenous regressors).
    kleads : int, default=0
        Number of leads for DOLS correction.
    
    Returns
    -------
    Q1 : float
        Robust cointegration test statistic (Q_r).
    Q2 : float
        Joint CI and cobreaking test statistic (Q_cb).
    Q3 : float
        Joint CI and cotrending test statistic (Q_ct).
    
    Notes
    -----
    This is an exact translation of CK_Qknown_new.m from Carrion-i-Silvestre
    and Kim (2019).
    
    Examples
    --------
    >>> import numpy as np
    >>> from co_eco import ck_test_known_breaks
    >>> np.random.seed(42)
    >>> T = 200
    >>> x = np.cumsum(np.random.randn(T, 1), axis=0)
    >>> y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T))
    >>> Q_r, Q_cb, Q_ct = ck_test_known_breaks(y, x, model=2, break_dates=[100])
    """
    # Ensure proper array shapes
    y = np.atleast_1d(y).flatten()
    x = np.atleast_2d(x)
    if x.shape[0] == 1 and x.shape[1] > 1:
        x = x.T
    
    T = len(y)
    px = x.shape[1]
    
    # Handle break dates
    if break_dates is None:
        break_dates = np.array([])
    else:
        break_dates = np.atleast_1d(break_dates).astype(int)
    m = len(break_dates)  # Number of structural breaks
    
    # Get lambda_hat if not provided
    if lambda_hat is None:
        lambda_hat = get_lambda_bar(m, model, px)
    
    # Compute theta_hat
    Theta_hat = 1 - lambda_hat / T
    
    # Generate deterministic regressors
    D0 = np.ones((T, 1))  # Intercept
    DT0 = np.arange(1, T + 1).reshape(-1, 1)  # Time trend
    
    # Generate step dummy variables
    DU = create_step_dummies(T, break_dates)
    
    # Compute adjustment factor for Model II
    if model == 1:
        adj = 0.0
    elif model == 2:
        # Construct d matrix
        if m > 0:
            d = np.column_stack([D0, DU, DT0])
        else:
            d = np.column_stack([D0, DT0])
        
        # First differences
        dd = d[1:, :] - d[:-1, :]
        dd = dd[:, 1:]  # Remove differenced constant
        dx = x[1:, :] - x[:-1, :]
        
        # Regression of dx on dd
        alphax = solve(dd.T @ dd, dd.T @ dx)
        cx = alphax[-1, :].reshape(-1, 1)  # Trend coefficient
        
        # Residuals
        dX0 = dx - dd @ alphax
        
        # AR(1) estimation
        dXl = dX0[:-1, :]
        dXh = dX0[1:, :]
        A = solve(dXl.T @ dXl, dXl.T @ dXh).T
        
        # Innovation covariance
        Ex = dXh - dXl @ A.T
        SG = (Ex.T @ Ex) / (T - 1)
        
        try:
            SGx = cholesky(SG).T  # Lower triangular Cholesky
            I_A = np.eye(A.shape[0]) - A
            term1 = cx.T @ inv(SGx) @ I_A @ cx
            term2 = cx.T @ cx
            adj = -2 * np.log(term1[0, 0]) + np.log(term2[0, 0])
        except:
            adj = 0.0
    else:
        raise ValueError(f"Invalid model: {model}. Must be 1 or 2.")
    
    # Prepare regressors depending on DOLS options
    if klags == 0 and kleads == 0:  # Exogenous regressors
        Tn = T
        if model == 1:
            if m > 0:
                W0 = np.column_stack([x, D0, DU])
            else:
                W0 = np.column_stack([x, D0])
            W0cb = np.column_stack([x, D0])
            W0ct = W0cb.copy()  # No cotrending test for Model I
        elif model == 2:
            if m > 0:
                W0 = np.column_stack([x, D0, DU, DT0])
            else:
                W0 = np.column_stack([x, D0, DT0])
            W0cb = np.column_stack([x, D0, DT0])
            W0ct = np.column_stack([x, D0])
    else:  # Endogenous regressors - use DOLS
        Tn = T - kleads - klags - 1
        
        # Trim y
        y = y[klags + 1:T - kleads]
        
        # Compute DOLS regressors
        U = dols_reg_maker(x, klags, kleads)
        
        # Trim other variables
        x = x[klags + 1:T - kleads, :]
        D0 = D0[klags + 1:T - kleads, :]
        if m > 0:
            DU = DU[klags + 1:T - kleads, :]
        DT0 = DT0[klags + 1:T - kleads, :]
        
        if model == 1:
            if m > 0:
                W0 = np.column_stack([x, D0, DU, U])
            else:
                W0 = np.column_stack([x, D0, U])
            W0cb = np.column_stack([x, D0, U])
            W0ct = W0cb.copy()
        elif model == 2:
            if m > 0:
                W0 = np.column_stack([x, D0, DU, DT0, U])
            else:
                W0 = np.column_stack([x, D0, DT0, U])
            W0cb = np.column_stack([x, D0, DT0, U])
            W0ct = np.column_stack([x, D0, U])
    
    # Compute (W'W) matrices
    WW0 = W0.T @ W0
    WW0cb = W0cb.T @ W0cb
    WW0ct = W0ct.T @ W0ct
    
    # Detrend y under different null hypotheses
    y0 = y - W0 @ solve(WW0, W0.T @ y)  # CI
    ycb = y - W0cb @ solve(WW0cb, W0cb.T @ y)  # CI & CB
    yct = y - W0ct @ solve(WW0ct, W0ct.T @ y)  # CI & CT
    
    # Long-run variance estimates with degrees of freedom adjustment
    s20 = long_run_variance(y0.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0.shape[1]))
    s2cb = long_run_variance(ycb.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0cb.shape[1]))
    s2ct = long_run_variance(yct.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0ct.shape[1]))
    
    # SSR under null
    ssr0 = y0.T @ y0
    ssrcb = ycb.T @ ycb
    ssrct = yct.T @ yct
    
    # Construct Psi^(1/2) matrix for quasi-differencing
    Psi_theta_hat = np.eye(Tn) + np.tril((1 - Theta_hat) * np.ones((Tn, Tn)), -1)
    
    # Transform y and W0 for the alternative model
    y1 = solve(Psi_theta_hat, y)
    W1 = solve(Psi_theta_hat, W0)
    WW1 = W1.T @ W1
    
    # Detrend under alternative (no cointegration)
    res1 = y1 - W1 @ solve(WW1, W1.T @ y1)
    ssr1 = res1.T @ res1
    
    # Compute test statistics
    Q1 = -2 * (-ssr0 / s20 / 2 - np.log(det(WW0)) / 2 + ssr1 / s20 / 2 + np.log(det(WW1)) / 2)
    Q2 = -2 * (-ssrcb / s2cb / 2 - np.log(det(WW0cb)) / 2 + ssr1 / s2cb / 2 + np.log(det(WW1)) / 2) + m * np.log(T)
    Q3 = -2 * (-ssrct / s2ct / 2 - np.log(det(WW0ct)) / 2 + ssr1 / s2ct / 2 + np.log(det(WW1)) / 2) + adj + (m + 2) * np.log(T)
    
    return float(Q1), float(Q2), float(Q3)


def ck_test_unknown_1break(
    y: np.ndarray,
    x: np.ndarray,
    model: int,
    lambda_hat: Optional[float] = None,
    klags: int = 0,
    kleads: int = 0,
    epsilon: float = 0.15
) -> Tuple[float, float, float, int]:
    """
    Quasi-likelihood ratio tests with unknown single break date.
    
    Computes the robust CI test (Q_r), joint CI/CB test (Q_cb), and 
    joint CI/CT test (Q_ct) when break date is unknown and estimated.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (T x 1).
    x : np.ndarray
        Stochastic regressors (T x px).
    model : int
        Model specification (1 or 2).
    lambda_hat : float, optional
        Local-to-unity parameter. If None, uses optimal value from tables.
    klags : int, default=0
        Number of lags for DOLS correction.
    kleads : int, default=0
        Number of leads for DOLS correction.
    epsilon : float, default=0.15
        Trimming parameter for break date search.
    
    Returns
    -------
    Q1 : float
        Robust cointegration test statistic (Q_r).
    Q2 : float
        Joint CI and cobreaking test statistic (Q_cb).
    Q3 : float
        Joint CI and cotrending test statistic (Q_ct).
    Tbhat : int
        Estimated break date (index).
    
    Notes
    -----
    This is an exact translation of CK_Qunknown1_Bdate.m.
    
    Examples
    --------
    >>> import numpy as np
    >>> from co_eco import ck_test_unknown_1break
    >>> np.random.seed(42)
    >>> T = 200
    >>> x = np.cumsum(np.random.randn(T, 1), axis=0)
    >>> y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T))
    >>> Q_r, Q_cb, Q_ct, Tb = ck_test_unknown_1break(y, x, model=2)
    """
    # Ensure proper array shapes
    y = np.atleast_1d(y).flatten()
    x = np.atleast_2d(x)
    if x.shape[0] == 1 and x.shape[1] > 1:
        x = x.T
    
    m = 1  # Number of breaks
    T = len(y)
    px = x.shape[1]
    epsi = epsilon
    
    # Get lambda_hat if not provided
    if lambda_hat is None:
        lambda_hat = get_lambda_bar(m, model, px)
    
    Theta_hat = 1 - lambda_hat / T
    
    # Generate deterministic regressors
    D0 = np.ones((T, 1))
    DT0 = np.arange(1, T + 1).reshape(-1, 1)
    
    # Store original x for adjustment calculation
    x_orig = x.copy()
    
    # Prepare regressors depending on options
    if klags == 0 and kleads == 0:  # Exogenous regressors
        Tn = T
        if model == 1:
            W0cb = np.column_stack([x, D0])
            W0ct = W0cb.copy()
        elif model == 2:
            W0cb = np.column_stack([x, D0, DT0])
            W0ct = np.column_stack([x, D0])
    else:  # Endogenous regressors
        Tn = T - kleads - klags - 1
        y = y[klags + 1:T - kleads]
        D0 = D0[klags + 1:T - kleads, :]
        DT0 = DT0[klags + 1:T - kleads, :]
        U = dols_reg_maker(x_orig, klags, kleads)
        x = x[klags + 1:T - kleads, :]
        
        if model == 1:
            W0cb = np.column_stack([x, D0, U])
            W0ct = W0cb.copy()
        elif model == 2:
            W0cb = np.column_stack([x, D0, DT0, U])
            W0ct = np.column_stack([x, D0, U])
    
    WW0cb = W0cb.T @ W0cb
    WW0ct = W0ct.T @ W0ct
    
    # Detrend y under CI & CB and CI & CT
    ycb = y - W0cb @ solve(WW0cb, W0cb.T @ y)
    yct = y - W0ct @ solve(WW0ct, W0ct.T @ y)
    
    # Long-run variance estimates
    s2cb = long_run_variance(ycb.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0cb.shape[1]))
    s2ct = long_run_variance(yct.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0ct.shape[1]))
    
    # Log-likelihood under CI & CB and CI & CT
    L0cb = -(ycb.T @ ycb) / s2cb / 2 - np.log(det(WW0cb)) / 2
    L0ct = -(yct.T @ yct) / s2ct / 2 - np.log(det(WW0ct)) / 2
    
    # First pass: find break date that minimizes SSR
    Tbtemp = 0
    SSR0 = ycb.T @ ycb
    
    trim_start = int(round(Tn * epsi)) + 1
    trim_end = Tn - int(round(Tn * epsi))
    
    for Tb in range(trim_start, trim_end):
        DU = np.zeros(Tn)
        DU[Tb:] = 1.0
        DU0 = DU - W0cb @ solve(WW0cb, W0cb.T @ DU)
        res0 = ycb - DU0 * ((DU0.T @ DU0) ** (-1) * (DU0.T @ ycb))
        SSRtemp = res0.T @ res0
        if SSRtemp < SSR0:
            SSR0 = SSRtemp
            Tbtemp = Tb
    
    # Compute s2temp using estimated break date
    DUhat = np.zeros(Tn)
    DUhat[Tbtemp:] = 1.0
    DUhat0 = DUhat - W0cb @ solve(WW0cb, W0cb.T @ DUhat)
    res0 = ycb - DUhat0 * ((DUhat0.T @ DUhat0) ** (-1) * (DUhat0.T @ ycb))
    s2temp = long_run_variance(res0.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0cb.shape[1] - 1))
    
    # Construct Psi matrix
    Psi_theta_hat = np.eye(Tn) + np.tril((1 - Theta_hat) * np.ones((Tn, Tn)), -1)
    
    # Transform y and W0cb for alternative
    y1 = solve(Psi_theta_hat, y)
    W1cb = solve(Psi_theta_hat, W0cb)
    WW1cb = W1cb.T @ W1cb
    y1cb = y1 - W1cb @ solve(WW1cb, W1cb.T @ y1)
    
    # Initialize max likelihoods
    maxL0 = L0cb - 1000 * np.abs(L0cb)
    maxL1 = -(y1cb.T @ y1cb) / s2cb / 2 - np.log(det(WW1cb)) / 2
    maxL1 = maxL1 - 1000 * np.abs(maxL1)
    maxL1cb = maxL1
    maxL1ct = -(y1cb.T @ y1cb) / s2ct / 2 - np.log(det(WW1cb)) / 2
    maxL1ct = maxL1ct - 1000 * np.abs(maxL1ct)
    
    Tbhat = 0
    
    # Main loop: search for break date
    for Tb in range(trim_start, trim_end):
        # Under null
        DU = np.zeros(Tn)
        DU[Tb:] = 1.0
        DU0 = DU - W0cb @ solve(WW0cb, W0cb.T @ DU)
        res0 = ycb - DU0 * ((DU0.T @ DU0) ** (-1) * (DU0.T @ ycb))
        L0temp = -(res0.T @ res0) / s2temp / 2 - np.log(det(WW0cb)) / 2 - np.log(DU0.T @ DU0) / 2
        
        if L0temp > maxL0:
            maxL0 = L0temp
            Tbhat = Tb
        
        # Under alternative
        DU1 = solve(Psi_theta_hat, DU)
        DU1 = DU1 - W1cb @ solve(WW1cb, W1cb.T @ DU1)
        res1 = y1cb - DU1 * ((DU1.T @ DU1) ** (-1) * (DU1.T @ y1cb))
        
        L1temp = -(res1.T @ res1) / s2temp / 2 - np.log(det(WW1cb)) / 2 - np.log(DU1.T @ DU1) / 2
        L1tempcb = -(res1.T @ res1) / s2cb / 2 - np.log(det(WW1cb)) / 2 - np.log(DU1.T @ DU1) / 2
        L1tempct = -(res1.T @ res1) / s2ct / 2 - np.log(det(WW1cb)) / 2 - np.log(DU1.T @ DU1) / 2
        
        maxL1 = max(maxL1, L1temp)
        maxL1cb = max(maxL1cb, L1tempcb)
        maxL1ct = max(maxL1ct, L1tempct)
    
    # Compute adjustment for Model II
    if model == 1:
        adj = 0.0
    elif model == 2:
        DUhat = np.zeros((Tn, 1))
        DUhat[Tbhat:, 0] = 1.0
        d = np.column_stack([D0, DUhat, DT0])
        dd = d[1:, :] - d[:-1, :]
        dd = dd[:, 1:]
        dx = x[1:, :] - x[:-1, :]
        
        alphax = solve(dd.T @ dd, dd.T @ dx)
        cx = alphax[-1, :].reshape(-1, 1)
        
        dX0 = dx - dd @ alphax
        dXl = dX0[:-1, :]
        dXh = dX0[1:, :]
        A = solve(dXl.T @ dXl, dXl.T @ dXh).T
        Ex = dXh - dXl @ A.T
        SG = (Ex.T @ Ex) / (T - 1)
        
        try:
            SGx = cholesky(SG).T
            I_A = np.eye(A.shape[0]) - A
            term1 = cx.T @ inv(SGx) @ I_A @ cx
            term2 = cx.T @ cx
            adj = -2 * np.log(term1[0, 0]) + np.log(term2[0, 0])
        except:
            adj = 0.0
    
    # Compute test statistics
    Q1 = float(-2 * (maxL0 - maxL1))
    Q2 = float(-2 * (L0cb - maxL1cb) + m * np.log(T))
    Q3 = float(-2 * (L0ct - maxL1ct) + adj + (m + 2) * np.log(T))
    
    return Q1, Q2, Q3, int(Tbhat)


def ck_test_unknown_2breaks(
    y: np.ndarray,
    x: np.ndarray,
    model: int,
    lambda_hat: Optional[float] = None,
    klags: int = 0,
    kleads: int = 0,
    epsilon: float = 0.15
) -> Tuple[float, float, float, np.ndarray]:
    """
    Quasi-likelihood ratio tests with unknown two break dates.
    
    Computes the robust CI test (Q_r), joint CI/CB test (Q_cb), and 
    joint CI/CT test (Q_ct) when two break dates are unknown and estimated.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (T x 1).
    x : np.ndarray
        Stochastic regressors (T x px).
    model : int
        Model specification (1 or 2).
    lambda_hat : float, optional
        Local-to-unity parameter. If None, uses optimal value from tables.
    klags : int, default=0
        Number of lags for DOLS correction.
    kleads : int, default=0
        Number of leads for DOLS correction.
    epsilon : float, default=0.15
        Trimming parameter for break date search.
    
    Returns
    -------
    Q1 : float
        Robust cointegration test statistic (Q_r).
    Q2 : float
        Joint CI and cobreaking test statistic (Q_cb).
    Q3 : float
        Joint CI and cotrending test statistic (Q_ct).
    Tbhat : np.ndarray
        Estimated break dates (2-element array).
    
    Notes
    -----
    This is an exact translation of CK_Qunknown2_Bdate.m.
    """
    # Ensure proper array shapes
    y = np.atleast_1d(y).flatten()
    x = np.atleast_2d(x)
    if x.shape[0] == 1 and x.shape[1] > 1:
        x = x.T
    
    m = 2  # Number of breaks
    T = len(y)
    px = x.shape[1]
    epsi = epsilon
    
    # Get lambda_hat if not provided
    if lambda_hat is None:
        lambda_hat = get_lambda_bar(m, model, px)
    
    Theta_hat = 1 - lambda_hat / T
    
    # Generate deterministic regressors
    D0 = np.ones((T, 1))
    DT0 = np.arange(1, T + 1).reshape(-1, 1)
    
    # Store original x
    x_orig = x.copy()
    
    # Prepare regressors
    if klags == 0 and kleads == 0:
        Tn = T
        if model == 1:
            W0cb = np.column_stack([x, D0])
            W0ct = W0cb.copy()
        elif model == 2:
            W0cb = np.column_stack([x, D0, DT0])
            W0ct = np.column_stack([x, D0])
    else:
        Tn = T - kleads - klags - 1
        y = y[klags + 1:T - kleads]
        D0 = D0[klags + 1:T - kleads, :]
        DT0 = DT0[klags + 1:T - kleads, :]
        U = dols_reg_maker(x_orig, klags, kleads)
        x = x[klags + 1:T - kleads, :]
        
        if model == 1:
            W0cb = np.column_stack([x, D0, U])
            W0ct = W0cb.copy()
        elif model == 2:
            W0cb = np.column_stack([x, D0, DT0, U])
            W0ct = np.column_stack([x, D0, U])
    
    WW0cb = W0cb.T @ W0cb
    WW0ct = W0ct.T @ W0ct
    
    # Detrend y
    ycb = y - W0cb @ solve(WW0cb, W0cb.T @ y)
    yct = y - W0ct @ solve(WW0ct, W0ct.T @ y)
    
    # Long-run variance
    s2cb = long_run_variance(ycb.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0cb.shape[1]))
    s2ct = long_run_variance(yct.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0ct.shape[1]))
    
    # Log-likelihoods under null
    L0cb = -(ycb.T @ ycb) / s2cb / 2 - np.log(det(WW0cb)) / 2
    L0ct = -(yct.T @ yct) / s2ct / 2 - np.log(det(WW0ct)) / 2
    
    # Pre-compute DU matrix (lower triangular of ones)
    DU0mat = np.tril(np.ones((Tn, Tn)))
    DU0mat = DU0mat - W0cb @ solve(WW0cb, W0cb.T @ DU0mat)
    
    # First pass: find break dates that minimize SSR
    Tbtemp = np.array([0, 0])
    SSR0 = ycb.T @ ycb
    DU0 = np.zeros((Tn, 2))
    
    trim = int(round(Tn * epsi))
    
    for Tb in range(trim + 1, Tn - trim * 2):
        DU0[:, 0] = DU0mat[:, Tb]
        for Tb2 in range(Tb + trim, Tn - trim):
            DU0[:, 1] = DU0mat[:, Tb2]
            coef = solve(DU0.T @ DU0, DU0.T @ ycb)
            res0 = ycb - DU0 @ coef
            SSRtemp = res0.T @ res0
            if SSRtemp < SSR0:
                SSR0 = SSRtemp
                Tbtemp = np.array([Tb, Tb2])
    
    # Compute s2temp
    DUhat = np.column_stack([DU0mat[:, Tbtemp[0]], DU0mat[:, Tbtemp[1]]])
    res0 = ycb - DUhat @ solve(DUhat.T @ DUhat, DUhat.T @ ycb)
    s2temp = long_run_variance(res0.reshape(-1, 1), 0)[0, 0] * ((Tn - 1) / (Tn - W0cb.shape[1] - 2))
    
    # Construct Psi matrix
    Psi_theta_hat = np.eye(Tn) + np.tril((1 - Theta_hat) * np.ones((Tn, Tn)), -1)
    
    # Transform for alternative
    y1 = solve(Psi_theta_hat, y)
    W1cb = solve(Psi_theta_hat, W0cb)
    WW1cb = W1cb.T @ W1cb
    y1cb = y1 - W1cb @ solve(WW1cb, W1cb.T @ y1)
    
    # Initialize
    maxL0 = L0cb - 1000 * np.abs(L0cb)
    maxL1 = -(y1cb.T @ y1cb) / s2cb / 2 - np.log(det(WW1cb)) / 2
    maxL1 = maxL1 - 1000 * np.abs(maxL1)
    maxL1cb = maxL1
    maxL1ct = -(y1cb.T @ y1cb) / s2ct / 2 - np.log(det(WW1cb)) / 2
    maxL1ct = maxL1ct - 1000 * np.abs(maxL1ct)
    
    Tbhat = np.array([0, 0])
    DU0 = np.zeros((Tn, 2))
    DU1 = np.zeros((Tn, 2))
    
    # Pre-compute transformed DU matrix
    DU1mat = solve(Psi_theta_hat, DU0mat + W0cb @ solve(WW0cb, W0cb.T @ DU0mat))
    DU1mat = DU1mat - W1cb @ solve(WW1cb, W1cb.T @ DU1mat)
    
    # Recompute DU0mat after transformation for correct indexing
    DU0mat_orig = np.tril(np.ones((Tn, Tn)))
    DU0mat = DU0mat_orig - W0cb @ solve(WW0cb, W0cb.T @ DU0mat_orig)
    
    DU1mat = solve(Psi_theta_hat, DU0mat_orig)
    DU1mat = DU1mat - W1cb @ solve(WW1cb, W1cb.T @ DU1mat)
    
    # Main search loop
    for Tb in range(trim + 1, Tn - trim * 2):
        DU0[:, 0] = DU0mat[:, Tb]
        DU1[:, 0] = DU1mat[:, Tb]
        
        for Tb2 in range(Tb + trim, Tn - trim):
            DU0[:, 1] = DU0mat[:, Tb2]
            
            # Under null
            coef0 = solve(DU0.T @ DU0, DU0.T @ ycb)
            res0 = ycb - DU0 @ coef0
            L0temp = -(res0.T @ res0) / s2temp / 2 - np.log(det(WW0cb)) / 2 - np.log(det(DU0.T @ DU0)) / 2
            
            if L0temp > maxL0:
                maxL0 = L0temp
                Tbhat = np.array([Tb, Tb2])
            
            # Under alternative
            DU1[:, 1] = DU1mat[:, Tb2]
            coef1 = solve(DU1.T @ DU1, DU1.T @ y1cb)
            res1 = y1cb - DU1 @ coef1
            
            DU1_det = det(DU1.T @ DU1)
            if DU1_det > 0:
                L1temp = -(res1.T @ res1) / s2temp / 2 - np.log(det(WW1cb)) / 2 - np.log(DU1_det) / 2
                L1tempcb = -(res1.T @ res1) / s2cb / 2 - np.log(det(WW1cb)) / 2 - np.log(DU1_det) / 2
                L1tempct = -(res1.T @ res1) / s2ct / 2 - np.log(det(WW1cb)) / 2 - np.log(DU1_det) / 2
                
                maxL1 = max(maxL1, L1temp)
                maxL1cb = max(maxL1cb, L1tempcb)
                maxL1ct = max(maxL1ct, L1tempct)
    
    # Compute adjustment for Model II
    if model == 1:
        adj = 0.0
    elif model == 2:
        DU0mat_orig = np.tril(np.ones((Tn, Tn)))
        DUhat = np.column_stack([DU0mat_orig[:, Tbhat[0]], DU0mat_orig[:, Tbhat[1]]])
        d = np.column_stack([D0, DUhat, DT0])
        dd = d[1:, :] - d[:-1, :]
        dd = dd[:, 1:]
        dx = x[1:, :] - x[:-1, :]
        
        alphax = solve(dd.T @ dd, dd.T @ dx)
        cx = alphax[-1, :].reshape(-1, 1)
        
        dX0 = dx - dd @ alphax
        dXl = dX0[:-1, :]
        dXh = dX0[1:, :]
        A = solve(dXl.T @ dXl, dXl.T @ dXh).T
        Ex = dXh - dXl @ A.T
        SG = (Ex.T @ Ex) / (T - 1)
        
        try:
            SGx = cholesky(SG).T
            I_A = np.eye(A.shape[0]) - A
            term1 = cx.T @ inv(SGx) @ I_A @ cx
            term2 = cx.T @ cx
            adj = -2 * np.log(term1[0, 0]) + np.log(term2[0, 0])
        except:
            adj = 0.0
    
    # Compute test statistics
    Q1 = float(-2 * (maxL0 - maxL1))
    Q2 = float(-2 * (L0cb - maxL1cb) + m * np.log(T))
    Q3 = float(-2 * (L0ct - maxL1ct) + adj + (m + 2) * np.log(T))
    
    return Q1, Q2, Q3, Tbhat


def dmax_cobreaking_test(
    results_by_m: List[Tuple[float, float, float]],
    model: int,
    px: int,
    T: int,
    M: int = 2
) -> DmaxTestResults:
    """
    Compute the Dmax cobreaking test.
    
    Parameters
    ----------
    results_by_m : list
        List of (Q_r, Q_cb, Q_ct) tuples for m=0,1,...,M.
    model : int
        Model specification (1 or 2).
    px : int
        Number of stochastic regressors.
    T : int
        Sample size.
    M : int, default=2
        Maximum number of breaks.
    
    Returns
    -------
    DmaxTestResults
        Results object containing Dmax statistic and component statistics.
    """
    params = get_dmax_params('dmax_cb', model, min(px, 2))
    
    component_stats = np.array([r[1] for r in results_by_m[:M+1]])  # Q_cb values
    normalized = np.zeros(M + 1)
    
    for m in range(M + 1):
        a_m, b_m = params[m, :]
        normalized[m] = (component_stats[m] - a_m) / b_m
    
    Q_dmax = np.max(normalized)
    
    cv_5 = get_dmax_critical_value('dmax_cb', model, px, 0.05)
    cv_1 = get_dmax_critical_value('dmax_cb', model, px, 0.01)
    
    return DmaxTestResults(
        Q_dmax=float(Q_dmax),
        test_type='dmax_cb',
        component_stats=component_stats,
        normalized_stats=normalized,
        model=model,
        max_breaks=M,
        num_regressors=px,
        sample_size=T,
        critical_values={0.05: cv_5, 0.01: cv_1}
    )


def dmax_cotrending_test(
    results_by_m: List[Tuple[float, float, float]],
    model: int,
    px: int,
    T: int,
    M: int = 2
) -> DmaxTestResults:
    """
    Compute the Dmax cotrending test.
    
    Parameters
    ----------
    results_by_m : list
        List of (Q_r, Q_cb, Q_ct) tuples for m=0,1,...,M.
    model : int
        Model specification (must be 2).
    px : int
        Number of stochastic regressors.
    T : int
        Sample size.
    M : int, default=2
        Maximum number of breaks.
    
    Returns
    -------
    DmaxTestResults
        Results object containing Dmax statistic and component statistics.
    """
    if model == 1:
        warnings.warn("Cotrending test not applicable for Model I.")
        return None
    
    params = get_dmax_params('dmax_ct', model, min(px, 2))
    
    component_stats = np.array([r[2] for r in results_by_m[:M+1]])  # Q_ct values
    normalized = np.zeros(M + 1)
    
    for m in range(M + 1):
        a_m, b_m = params[m, :]
        if b_m > 0:
            normalized[m] = (component_stats[m] - a_m) / b_m
        else:
            normalized[m] = -np.inf
    
    Q_dmax = np.max(normalized)
    
    cv_5 = get_dmax_critical_value('dmax_ct', model, px, 0.05)
    cv_1 = get_dmax_critical_value('dmax_ct', model, px, 0.01)
    
    return DmaxTestResults(
        Q_dmax=float(Q_dmax),
        test_type='dmax_ct',
        component_stats=component_stats,
        normalized_stats=normalized,
        model=model,
        max_breaks=M,
        num_regressors=px,
        sample_size=T,
        critical_values={0.05: cv_5, 0.01: cv_1}
    )


class CKTest:
    """
    Main class for Carrion-i-Silvestre and Kim (2019) cointegration tests.
    
    This class provides a convenient interface for running all the tests
    with automatic handling of critical values and result formatting.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable.
    x : np.ndarray
        Stochastic regressors.
    model : int
        Model specification:
        - 1: Mean shifts only
        - 2: Linear trend with intercept shifts
    klags : int, default=0
        Number of lags for DOLS correction.
    kleads : int, default=0
        Number of leads for DOLS correction.
    
    Attributes
    ----------
    y : np.ndarray
        Dependent variable.
    x : np.ndarray
        Stochastic regressors.
    model : int
        Model specification.
    T : int
        Sample size.
    px : int
        Number of regressors.
    klags : int
        DOLS lags.
    kleads : int
        DOLS leads.
    
    Examples
    --------
    >>> import numpy as np
    >>> from co_eco import CKTest
    >>> np.random.seed(42)
    >>> T = 200
    >>> x = np.cumsum(np.random.randn(T, 1), axis=0)
    >>> y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T))
    >>> 
    >>> test = CKTest(y, x, model=2, klags=2, kleads=2)
    >>> results = test.run(num_breaks=1)
    >>> print(results)
    """
    
    def __init__(
        self,
        y: np.ndarray,
        x: np.ndarray,
        model: int,
        klags: int = 0,
        kleads: int = 0
    ):
        self.y = np.atleast_1d(y).flatten()
        self.x = np.atleast_2d(x)
        if self.x.shape[0] == 1 and self.x.shape[1] > 1:
            self.x = self.x.T
        
        self.model = model
        self.T = len(self.y)
        self.px = self.x.shape[1]
        self.klags = klags
        self.kleads = kleads
        
        if model not in [1, 2]:
            raise ValueError("Model must be 1 or 2.")
    
    def run(
        self,
        num_breaks: int = 1,
        break_dates: Optional[Union[List[int], np.ndarray]] = None,
        lambda_hat: Optional[float] = None
    ) -> CKTestResults:
        """
        Run the cointegration tests.
        
        Parameters
        ----------
        num_breaks : int, default=1
            Number of structural breaks to consider (0, 1, or 2).
        break_dates : list or np.ndarray, optional
            Known break dates. If None, break dates are estimated.
        lambda_hat : float, optional
            Local-to-unity parameter. If None, uses optimal value.
        
        Returns
        -------
        CKTestResults
            Results object containing test statistics and critical values.
        """
        if break_dates is not None:
            # Known break dates
            Q_r, Q_cb, Q_ct = ck_test_known_breaks(
                self.y, self.x, self.model, break_dates,
                lambda_hat, self.klags, self.kleads
            )
            break_dates = np.atleast_1d(break_dates)
            Tbhat = break_dates
        else:
            # Unknown break dates
            if num_breaks == 0:
                Q_r, Q_cb, Q_ct = ck_test_known_breaks(
                    self.y, self.x, self.model, None,
                    lambda_hat, self.klags, self.kleads
                )
                Tbhat = None
            elif num_breaks == 1:
                Q_r, Q_cb, Q_ct, Tbhat = ck_test_unknown_1break(
                    self.y, self.x, self.model,
                    lambda_hat, self.klags, self.kleads
                )
                Tbhat = np.array([Tbhat])
            elif num_breaks == 2:
                Q_r, Q_cb, Q_ct, Tbhat = ck_test_unknown_2breaks(
                    self.y, self.x, self.model,
                    lambda_hat, self.klags, self.kleads
                )
            else:
                raise ValueError("num_breaks must be 0, 1, or 2.")
        
        # Get critical values
        critical_values = {
            'robust_ci': dict(zip(
                [0.10, 0.05, 0.01],
                get_all_critical_values('robust_ci', num_breaks, self.model, self.px)
            )),
            'joint_cb': dict(zip(
                [0.10, 0.05, 0.01],
                get_all_critical_values('joint_cb', num_breaks, self.model, self.px)
            )),
        }
        
        if self.model == 2:
            critical_values['joint_ct'] = dict(zip(
                [0.10, 0.05, 0.01],
                get_all_critical_values('joint_ct', num_breaks, self.model, self.px)
            ))
        
        # Calculate break fractions
        if Tbhat is not None:
            # Adjust for DOLS trimming
            if self.klags > 0 or self.kleads > 0:
                Tbhat_adjusted = Tbhat + (self.klags + 1)
            else:
                Tbhat_adjusted = Tbhat
            break_fractions = Tbhat_adjusted / self.T
        else:
            break_fractions = None
        
        return CKTestResults(
            Q_r=Q_r,
            Q_cb=Q_cb,
            Q_ct=Q_ct,
            break_dates=Tbhat,
            break_fractions=break_fractions,
            model=self.model,
            num_breaks=num_breaks,
            num_regressors=self.px,
            sample_size=self.T,
            klags=self.klags,
            kleads=self.kleads,
            critical_values=critical_values
        )
    
    def run_all(
        self,
        max_breaks: int = 2
    ) -> dict:
        """
        Run tests for all numbers of breaks from 0 to max_breaks.
        
        Parameters
        ----------
        max_breaks : int, default=2
            Maximum number of breaks to consider.
        
        Returns
        -------
        dict
            Dictionary mapping num_breaks to CKTestResults.
        """
        results = {}
        for m in range(max_breaks + 1):
            results[m] = self.run(num_breaks=m)
        return results
    
    def run_dmax(
        self,
        max_breaks: int = 2
    ) -> Tuple[DmaxTestResults, Optional[DmaxTestResults]]:
        """
        Run Dmax tests for cobreaking and cotrending.
        
        Parameters
        ----------
        max_breaks : int, default=2
            Maximum number of breaks to consider.
        
        Returns
        -------
        tuple
            (DmaxTestResults for cobreaking, DmaxTestResults for cotrending)
            Cotrending result is None for Model I.
        """
        # Collect results for each m
        results_by_m = []
        for m in range(max_breaks + 1):
            result = self.run(num_breaks=m)
            results_by_m.append((result.Q_r, result.Q_cb, result.Q_ct))
        
        dmax_cb = dmax_cobreaking_test(
            results_by_m, self.model, self.px, self.T, max_breaks
        )
        
        if self.model == 2:
            dmax_ct = dmax_cotrending_test(
                results_by_m, self.model, self.px, self.T, max_breaks
            )
        else:
            dmax_ct = None
        
        return dmax_cb, dmax_ct
