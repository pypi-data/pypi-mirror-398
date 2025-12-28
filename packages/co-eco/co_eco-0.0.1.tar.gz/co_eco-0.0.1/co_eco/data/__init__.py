"""
Data module for co-eco package.

Contains sample datasets and lambda bar tables.
"""

import os
import numpy as np
from typing import Tuple

_DATA_DIR = os.path.dirname(__file__)


def load_us_budget() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load US government budget data.
    
    Returns quarterly US government revenues and expenditures as 
    percentages of GDP from 1947.I to 2010.II.
    
    Returns
    -------
    revenues : np.ndarray
        Government revenues as % of GDP.
    expenditures : np.ndarray
        Government expenditures as % of GDP.
    balance : np.ndarray
        Budget balance (revenues - expenditures).
    
    Examples
    --------
    >>> from co_eco.data import load_us_budget
    >>> R, E, B = load_us_budget()
    >>> print(f"Sample size: {len(R)}")
    Sample size: 254
    """
    data_path = os.path.join(_DATA_DIR, 'USbudget.txt')
    data = np.loadtxt(data_path)
    
    revenues = data[:, 0] * 100  # Convert to percentage
    expenditures = data[:, 1] * 100
    balance = revenues - expenditures
    
    return revenues, expenditures, balance


def get_data_path(filename: str) -> str:
    """Get full path to a data file."""
    return os.path.join(_DATA_DIR, filename)
