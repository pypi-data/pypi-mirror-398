"""
Utility functions for the co-eco package.

This module contains helper functions for:
- Long-run variance estimation using Andrews (1991) automatic bandwidth selection
- DOLS regression matrix construction
- Step dummy variable creation

These functions are exact Python translations of the original MATLAB code by
Carrion-i-Silvestre and Kim (2019).
"""

import numpy as np
from numpy.linalg import solve, det, cholesky, inv
from typing import Tuple, Optional, Union
import warnings


def long_run_variance(
    vhat: np.ndarray,
    c: int = 0
) -> np.ndarray:
    """
    Estimate the long-run variance using the quadratic spectral kernel.
    
    Implements the HAC (Heteroskedasticity and Autocorrelation Consistent)
    covariance estimator with automatic bandwidth selection following
    Andrews (1991) using AR(1) approximation.
    
    Parameters
    ----------
    vhat : np.ndarray
        T x n matrix of residuals, where T is the number of observations
        and n is the number of variables.
    c : int, default=0
        Indicator for intercept term:
        - c=0: no intercept term in residuals
        - c=1: intercept term in residuals (assumed to be first column)
    
    Returns
    -------
    np.ndarray
        n x n long-run variance-covariance matrix estimate (2*pi*h(0)).
    
    Notes
    -----
    This is an exact translation of the MATLAB function longvar.m from
    Carrion-i-Silvestre and Kim (2019).
    
    The bandwidth is selected using the data-dependent method of Andrews (1991)
    with AR(1) approximation.
    
    References
    ----------
    Andrews, D.W.K. (1991). Heteroskedasticity and Autocorrelation Consistent
    Covariance Matrix Estimation. Econometrica, 59(3), 817-858.
    
    Examples
    --------
    >>> import numpy as np
    >>> from co_eco.utils import long_run_variance
    >>> np.random.seed(42)
    >>> residuals = np.random.randn(100, 1)
    >>> lrv = long_run_variance(residuals, c=0)
    """
    vhat = np.atleast_2d(vhat)
    if vhat.ndim == 1:
        vhat = vhat.reshape(-1, 1)
    
    T, n = vhat.shape
    
    # Compute all autocovariances
    Gamma = np.zeros((T * n, n))
    
    for j in range(T):
        gamma = (1 / T) * vhat[j:T, :].T @ vhat[:T-j, :]
        Gamma[n*j:n*(j+1), :] = gamma
    
    # Selection of bandwidth using AR(1) approximation (Andrews, 1991)
    rho = np.zeros(n - c)
    sig = np.zeros(n - c)
    
    for i in range(c, n):
        v = vhat[:, i]
        vh = v[1:T]
        vl = v[:T-1]
        
        # AR(1) coefficient
        r = (vl @ vl) ** (-1) * (vl @ vh)
        rho[i - c] = r
        
        # Innovation variance
        e = vh - vl * r
        sig[i - c] = (e @ e) / T
    
    # Compute optimal bandwidth parameter alpha
    numerator = 0.0
    denominator = 0.0
    
    for idx in range(n - c):
        numerator += 4 * (rho[idx] ** 2) * (sig[idx] ** 2) / ((1 - rho[idx]) ** 8)
        denominator += (sig[idx] ** 2) / ((1 - rho[idx]) ** 4)
    
    # Avoid division by zero
    if denominator == 0:
        alpha = 0
    else:
        alpha = numerator / denominator
    
    # Andrews (1991) optimal bandwidth for QS kernel
    m = 1.3221 * (alpha * T) ** (1/5)
    
    # Apply Quadratic Spectral (QS) kernel
    S = Gamma[:n, :].copy()
    
    for ind in range(1, T):
        d = 6 * np.pi * (ind / m) / 5
        if np.abs(d) > 1e-10:
            w = 3 * (np.sin(d) / d - np.cos(d)) / (d ** 2)
        else:
            w = 1.0
        S = S + w * Gamma[ind*n:ind*n+n, :]
    
    for ind in range(1, T):
        d = 6 * np.pi * (-ind / m) / 5
        if np.abs(d) > 1e-10:
            w = 3 * (np.sin(d) / d - np.cos(d)) / (d ** 2)
        else:
            w = 1.0
        S = S + w * Gamma[ind*n:ind*n+n, :].T
    
    # Degrees of freedom adjustment
    Shat = S * (T / (T - n))
    
    return Shat


def dols_reg_maker(
    x: np.ndarray,
    klags: int,
    kleads: int
) -> np.ndarray:
    """
    Create the DOLS (Dynamic OLS) regressor matrix.
    
    Constructs the matrix of leads and lags of first-differenced regressors
    for Dynamic OLS estimation as proposed by Saikkonen (1991).
    
    Parameters
    ----------
    x : np.ndarray
        T x px matrix of stochastic regressors, where T is the number of
        observations and px is the number of regressors.
    klags : int
        Number of lags of differenced regressors to include.
    kleads : int
        Number of leads of differenced regressors to include.
    
    Returns
    -------
    np.ndarray
        Tn x (px * (klags + kleads + 1)) matrix of differenced regressors
        with leads and lags, where Tn = T - kleads - klags - 1.
    
    Notes
    -----
    This is an exact translation of the MATLAB function DOLS_reg_maker.m
    from Carrion-i-Silvestre and Kim (2019).
    
    References
    ----------
    Saikkonen, P. (1991). Asymptotically Efficient Estimation of Cointegration
    Regressions. Econometric Theory, 7(1), 1-21.
    
    Examples
    --------
    >>> import numpy as np
    >>> from co_eco.utils import dols_reg_maker
    >>> x = np.random.randn(100, 2)
    >>> U = dols_reg_maker(x, klags=2, kleads=2)
    >>> U.shape
    (95, 10)
    """
    x = np.atleast_2d(x)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    
    T = x.shape[0]
    Tn = T - kleads - klags - 1
    
    # First difference of x
    dx = x[1:, :] - x[:-1, :]
    
    # Initialize with first set of differences
    U = dx[:Tn, :].copy()
    
    # Add leads and lags
    for idx in range(1, kleads + klags + 1):
        U = np.hstack([U, dx[idx:Tn+idx, :]])
    
    return U


def create_step_dummies(
    T: int,
    break_dates: Union[list, np.ndarray, None]
) -> np.ndarray:
    """
    Create step (level shift) dummy variables for structural breaks.
    
    Generates DU_t(T_i) = 1 for t > T_i and 0 elsewhere, for each break date.
    
    Parameters
    ----------
    T : int
        Total number of observations.
    break_dates : list, np.ndarray, or None
        Array of break dates (indices). If None or empty, returns empty array.
    
    Returns
    -------
    np.ndarray
        T x m matrix of step dummy variables, where m is the number of breaks.
        Each column contains 0s before the break and 1s after.
    
    Examples
    --------
    >>> from co_eco.utils import create_step_dummies
    >>> DU = create_step_dummies(T=100, break_dates=[30, 70])
    >>> DU.shape
    (100, 2)
    >>> DU[29, 0], DU[30, 0]  # Before and at first break
    (0.0, 0.0)
    >>> DU[31, 0]  # After first break
    1.0
    """
    if break_dates is None or len(break_dates) == 0:
        return np.array([]).reshape(T, 0)
    
    break_dates = np.atleast_1d(break_dates)
    m = len(break_dates)
    DU = np.zeros((T, m))
    
    for j, Tb in enumerate(break_dates):
        Tb = int(Tb)
        DU[Tb+1:, j] = 1.0
    
    return DU


def compute_adjustment_factor(
    x: np.ndarray,
    D0: np.ndarray,
    DU: np.ndarray,
    DT0: np.ndarray,
    T: int
) -> float:
    """
    Compute the adjustment factor for cotrending tests in Model II.
    
    This adjustment accounts for the presence of a linear trend in the
    regressors and is necessary for proper asymptotic distribution.
    
    Parameters
    ----------
    x : np.ndarray
        T x px matrix of stochastic regressors.
    D0 : np.ndarray
        T x 1 vector of ones (intercept).
    DU : np.ndarray
        T x m matrix of step dummy variables.
    DT0 : np.ndarray
        T x 1 time trend vector.
    T : int
        Number of observations.
    
    Returns
    -------
    float
        Adjustment factor for the test statistic.
    
    Notes
    -----
    This computes: -2*log(cx' * inv(SGx) * (I-A) * cx) + log(cx' * cx)
    where cx is the trend coefficient, A is the AR coefficient matrix,
    and SGx is the Cholesky factor of the innovation covariance.
    """
    x = np.atleast_2d(x)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    
    # Construct deterministic component
    if DU.size > 0:
        d = np.column_stack([D0, DU, DT0])
    else:
        d = np.column_stack([D0, DT0])
    
    # First differences
    dd = d[1:, :] - d[:-1, :]
    dd = dd[:, 1:]  # Remove constant differenced (becomes zero)
    dx = x[1:, :] - x[:-1, :]
    
    # Regression of dx on dd to get trend coefficient
    alphax = solve(dd.T @ dd, dd.T @ dx)
    cx = alphax[-1, :].reshape(-1, 1)  # Trend coefficient
    
    # Residuals
    dX0 = dx - dd @ alphax
    
    # AR(1) estimation for residuals
    dXl = dX0[:-1, :]
    dXh = dX0[1:, :]
    A = solve(dXl.T @ dXl, dXl.T @ dXh).T
    
    # Innovation covariance
    Ex = dXh - dXl @ A.T
    SG = (Ex.T @ Ex) / (T - 1)
    
    try:
        SGx = cholesky(SG).T  # Lower triangular
    except np.linalg.LinAlgError:
        # If not positive definite, use eigenvalue decomposition
        eigvals, eigvecs = np.linalg.eigh(SG)
        eigvals = np.maximum(eigvals, 1e-10)
        SGx = eigvecs @ np.diag(np.sqrt(eigvals))
    
    # Compute adjustment
    I_A = np.eye(A.shape[0]) - A
    
    try:
        term1 = cx.T @ inv(SGx) @ I_A @ cx
        term2 = cx.T @ cx
        
        if term1 > 0 and term2 > 0:
            adj = -2 * np.log(term1[0, 0]) + np.log(term2[0, 0])
        else:
            adj = 0.0
    except:
        adj = 0.0
    
    return adj


def ols_detrend(
    y: np.ndarray,
    W: np.ndarray
) -> np.ndarray:
    """
    OLS detrending: compute residuals y - W*(W'W)^(-1)*W'y.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable vector (T x 1).
    W : np.ndarray
        Regressor matrix (T x k).
    
    Returns
    -------
    np.ndarray
        OLS residuals (T x 1).
    """
    WW = W.T @ W
    coef = solve(WW, W.T @ y)
    return y - W @ coef


def quasi_difference_transform(
    y: np.ndarray,
    theta_hat: float
) -> np.ndarray:
    """
    Apply quasi-difference transformation using Psi^(-1/2).
    
    The transformation matrix Psi^(1/2) is lower triangular with 1 on
    the diagonal and (1-theta) off the diagonal. This function applies
    the inverse transformation.
    
    Parameters
    ----------
    y : np.ndarray
        Vector to transform (T x 1 or T x k).
    theta_hat : float
        Quasi-differencing parameter (= 1 - lambda_hat/T).
    
    Returns
    -------
    np.ndarray
        Transformed vector.
    """
    y = np.atleast_2d(y)
    if y.ndim == 1:
        y = y.reshape(-1, 1)
    
    T = y.shape[0]
    
    # Construct Psi^(1/2) matrix
    Psi = np.eye(T) + np.tril((1 - theta_hat) * np.ones((T, T)), -1)
    
    # Solve Psi * y_transformed = y for y_transformed
    return solve(Psi, y)


def matrix_fprintf(
    filename: str,
    A: np.ndarray
) -> None:
    """
    Write matrix to file in space-separated format.
    
    Parameters
    ----------
    filename : str
        Output file path.
    A : np.ndarray
        Matrix to write.
    
    Notes
    -----
    This is a translation of MatrixFprintf.m from the original code.
    """
    np.savetxt(filename, A, fmt='%f', delimiter=' ')
