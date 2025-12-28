"""
co-eco: Quasi-likelihood ratio tests for cointegration, cobreaking, and cotrending
===================================================================================

A Python implementation of the econometric tests proposed by 
Carrion-i-Silvestre and Kim (2019) for testing cointegration, cobreaking, 
and cotrending in time series data with structural breaks.

Reference
---------
Carrion-i-Silvestre, J.L. and Kim, D. (2019). Quasi-likelihood ratio tests 
for cointegration, cobreaking, and cotrending. Econometric Reviews, 
DOI: 10.1080/07474938.2018.1528416

Author
------
Dr Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/coeco

Version
-------
0.0.1

License
-------
MIT License
"""

__version__ = "0.0.1"
__author__ = "Dr Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

from co_eco.core import (
    CKTest,
    ck_test_known_breaks,
    ck_test_unknown_1break,
    ck_test_unknown_2breaks,
    dmax_cobreaking_test,
    dmax_cotrending_test,
)
from co_eco.utils import (
    long_run_variance,
    dols_reg_maker,
    create_step_dummies,
)
from co_eco.critical_values import (
    get_lambda_bar,
    get_critical_values,
    LAMBDA_BAR_TABLES,
    CRITICAL_VALUES,
)
from co_eco.results import CKTestResults, DmaxTestResults

__all__ = [
    # Main test class
    "CKTest",
    # Test functions
    "ck_test_known_breaks",
    "ck_test_unknown_1break",
    "ck_test_unknown_2breaks",
    "dmax_cobreaking_test",
    "dmax_cotrending_test",
    # Utility functions
    "long_run_variance",
    "dols_reg_maker",
    "create_step_dummies",
    # Critical values
    "get_lambda_bar",
    "get_critical_values",
    "LAMBDA_BAR_TABLES",
    "CRITICAL_VALUES",
    # Results classes
    "CKTestResults",
    "DmaxTestResults",
]
