# co-eco

**Quasi-likelihood ratio tests for cointegration, cobreaking, and cotrending**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python implementation of the econometric tests proposed by Carrion-i-Silvestre and Kim (2019) for testing cointegration, cobreaking, and cotrending in time series data with structural breaks.

## Overview

This package provides three types of tests:

1. **Robust Cointegration Test (Q_r)**: Tests the null hypothesis of cointegration regardless of whether structural breaks are present (robust to the presence or absence of breaks).

2. **Joint CI/CB Test (Q_cb)**: Tests the joint null hypothesis of cointegration AND cobreaking (breaks cancel out).

3. **Joint CI/CT Test (Q_ct)**: Tests the joint null hypothesis of cointegration AND cotrending (both breaks and linear trends cancel out). Only applicable for Model II.

Additionally, **Dmax tests** are provided for determining the number of breaks when testing cobreaking or cotrending.

## Installation

```bash
pip install co-eco
```

Or install from source:

```bash
git clone https://github.com/merwanroudane/coeco.git
cd coeco
pip install -e .
```

## Quick Start

```python
import numpy as np
from co_eco import CKTest

# Generate example data
np.random.seed(42)
T = 200
x = np.cumsum(np.random.randn(T, 1), axis=0)  # I(1) regressor
y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T))  # Cointegrated

# Run tests
test = CKTest(y, x, model=2, klags=2, kleads=2)
results = test.run(num_breaks=1)

# Display results
print(results)
```

## Detailed Usage

### Model Specifications

- **Model I**: Mean shifts only (no linear trend)
- **Model II**: Linear trend with intercept shifts

### Known Break Dates

```python
from co_eco import ck_test_known_breaks

Q_r, Q_cb, Q_ct = ck_test_known_breaks(
    y, x, 
    model=2, 
    break_dates=[100],  # Known break at t=100
    klags=2, 
    kleads=2
)
```

### Unknown Break Dates

```python
from co_eco import ck_test_unknown_1break, ck_test_unknown_2breaks

# One unknown break
Q_r, Q_cb, Q_ct, Tbhat = ck_test_unknown_1break(y, x, model=2, klags=2, kleads=2)

# Two unknown breaks
Q_r, Q_cb, Q_ct, Tbhat = ck_test_unknown_2breaks(y, x, model=2, klags=2, kleads=2)
```

### Using the CKTest Class

```python
from co_eco import CKTest

test = CKTest(y, x, model=2, klags=2, kleads=2)

# Run for specific number of breaks
results_1break = test.run(num_breaks=1)
print(results_1break.is_cointegrated(0.05))  # True if CI holds at 5% level

# Run for all break specifications (0, 1, 2)
all_results = test.run_all(max_breaks=2)

# Run Dmax tests
dmax_cb, dmax_ct = test.run_dmax(max_breaks=2)
print(dmax_cb)
```

### Output Formats

```python
# Get summary
print(results.summary())

# Get LaTeX table
latex_table = results.to_latex()

# Get dictionary
results_dict = results.to_dict()
```

## Example: US Budget Sustainability

```python
from co_eco import CKTest
from co_eco.data import load_us_budget

# Load data
R, E, B = load_us_budget()

# Test for cointegration between expenditures and revenues
test = CKTest(E, R.reshape(-1, 1), model=2, klags=3, kleads=3)

# Run tests with 1 break
results = test.run(num_breaks=1)
print(results)

# Run tests with 2 breaks
results_2 = test.run(num_breaks=2)
print(results_2)
```

## Critical Values

Critical values are provided for:
- Significance levels: 1%, 5%, 10%
- Number of breaks: 0, 1, 2
- Number of regressors: 1-5
- Both Model I and Model II

```python
from co_eco import get_critical_values, get_lambda_bar

# Get critical value
cv = get_critical_values('robust_ci', m=1, model=2, px=1, significance_level=0.05)

# Get lambda bar parameter
lbar = get_lambda_bar(m=1, model=2, px=1)
```

## API Reference

### Main Functions

| Function | Description |
|----------|-------------|
| `ck_test_known_breaks()` | Tests with known break dates |
| `ck_test_unknown_1break()` | Tests with one unknown break |
| `ck_test_unknown_2breaks()` | Tests with two unknown breaks |
| `dmax_cobreaking_test()` | Dmax test for cobreaking |
| `dmax_cotrending_test()` | Dmax test for cotrending |

### Utility Functions

| Function | Description |
|----------|-------------|
| `long_run_variance()` | HAC estimator with Andrews bandwidth |
| `dols_reg_maker()` | DOLS regressor matrix construction |
| `create_step_dummies()` | Step dummy variable creation |

### Classes

| Class | Description |
|-------|-------------|
| `CKTest` | Main class for running all tests |
| `CKTestResults` | Results container with formatting |
| `DmaxTestResults` | Dmax test results container |

## Mathematical Background

The tests are based on quasi-likelihood ratio principles. Under the null hypothesis of cointegration:

$$y_t = \beta' x_t + \alpha' d_t + v_t$$

where:
- $y_t$ is the dependent variable
- $x_t$ are stochastic regressors (I(1))
- $d_t$ are deterministic components (intercepts, trends, step dummies)
- $v_t$ is I(0) under cointegration, I(1) under no cointegration

The test statistics are:

- **Q_r**: Robust CI test (invariant to break parameters)
- **Q_cb**: Joint test with $m \log(T)$ adjustment
- **Q_ct**: Joint test with additional adjustment for trend

## Compatibility

This package is an exact translation of the original MATLAB code by Carrion-i-Silvestre and Kim (2019). Results should match the MATLAB implementation up to numerical precision.

## Citation

If you use this package in your research, please cite:

```bibtex
@article{carrion2019quasi,
  title={Quasi-likelihood ratio tests for cointegration, cobreaking, and cotrending},
  author={Carrion-i-Silvestre, Josep Llu{\'\i}s and Kim, Dukpa},
  journal={Econometric Reviews},
  volume={38},
  number={6},
  pages={681--709},
  year={2019},
  publisher={Taylor \& Francis},
  doi={10.1080/07474938.2018.1528416}
}
```

And this Python implementation:

```bibtex
@software{coeco2024,
  author = {Roudane, Merwan},
  title = {co-eco: Python implementation of Carrion-i-Silvestre and Kim (2019) cointegration tests},
  year = {2024},
  url = {https://github.com/merwanroudane/coeco}
}
```

## References

- Carrion-i-Silvestre, J.L. and Kim, D. (2019). Quasi-likelihood ratio tests for cointegration, cobreaking, and cotrending. *Econometric Reviews*, 38(6), 681-709.
- Andrews, D.W.K. (1991). Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation. *Econometrica*, 59(3), 817-858.
- Saikkonen, P. (1991). Asymptotically Efficient Estimation of Cointegration Regressions. *Econometric Theory*, 7(1), 1-21.

## Author

**Dr Merwan Roudane**  
Email: merwanroudane920@gmail.com  
GitHub: [https://github.com/merwanroudane/coeco](https://github.com/merwanroudane/coeco)

## License

MIT License - see [LICENSE](LICENSE) for details.
