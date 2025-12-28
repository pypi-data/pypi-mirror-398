"""
Results classes for the co-eco package.

This module provides structured output classes for test results that can be
easily displayed, exported, or used in further analysis.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import warnings

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


@dataclass
class CKTestResults:
    """
    Results container for Carrion-i-Silvestre and Kim cointegration tests.
    
    Attributes
    ----------
    Q_r : float
        Robust cointegration test statistic.
    Q_cb : float
        Joint CI and cobreaking test statistic.
    Q_ct : float
        Joint CI and cotrending test statistic.
    break_dates : np.ndarray or None
        Estimated break dates (indices).
    break_fractions : np.ndarray or None
        Estimated break fractions (dates/T).
    model : int
        Model specification (1 or 2).
    num_breaks : int
        Number of breaks (m).
    num_regressors : int
        Number of stochastic regressors (px).
    sample_size : int
        Sample size (T).
    klags : int
        Number of lags in DOLS.
    kleads : int
        Number of leads in DOLS.
    long_run_variance : float
        Estimated long-run variance.
    critical_values : dict
        Dictionary of critical values at different significance levels.
    """
    
    Q_r: float
    Q_cb: float
    Q_ct: float
    break_dates: Optional[np.ndarray]
    break_fractions: Optional[np.ndarray]
    model: int
    num_breaks: int
    num_regressors: int
    sample_size: int
    klags: int = 0
    kleads: int = 0
    long_run_variance: float = np.nan
    critical_values: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate inputs and compute derived quantities."""
        if self.break_fractions is None and self.break_dates is not None:
            self.break_fractions = np.array(self.break_dates) / self.sample_size
    
    def _get_significance(self, stat: float, test_type: str) -> str:
        """Determine significance level for a statistic."""
        cv = self.critical_values.get(test_type, {})
        if not cv:
            return ""
        
        if stat > cv.get(0.01, np.inf):
            return "***"
        elif stat > cv.get(0.05, np.inf):
            return "**"
        elif stat > cv.get(0.10, np.inf):
            return "*"
        return ""
    
    def _format_stat(self, stat: float, test_type: str) -> str:
        """Format statistic with significance stars."""
        sig = self._get_significance(stat, test_type)
        return f"{stat:.4f}{sig}"
    
    def is_cointegrated(self, significance_level: float = 0.05) -> bool:
        """
        Test if null hypothesis of cointegration is rejected.
        
        Parameters
        ----------
        significance_level : float
            Significance level (0.01, 0.05, or 0.10).
        
        Returns
        -------
        bool
            True if null is NOT rejected (cointegration holds).
        """
        cv = self.critical_values.get('robust_ci', {}).get(significance_level)
        if cv is None:
            warnings.warn("Critical values not available.")
            return None
        return self.Q_r <= cv
    
    def is_cobreaking(self, significance_level: float = 0.05) -> bool:
        """
        Test if joint null of CI and cobreaking is rejected.
        
        Parameters
        ----------
        significance_level : float
            Significance level.
        
        Returns
        -------
        bool
            True if null is NOT rejected (CI and CB hold).
        """
        cv = self.critical_values.get('joint_cb', {}).get(significance_level)
        if cv is None:
            warnings.warn("Critical values not available.")
            return None
        return self.Q_cb <= cv
    
    def is_cotrending(self, significance_level: float = 0.05) -> bool:
        """
        Test if joint null of CI and cotrending is rejected.
        
        Parameters
        ----------
        significance_level : float
            Significance level.
        
        Returns
        -------
        bool
            True if null is NOT rejected (CI and CT hold).
        """
        if self.model == 1:
            warnings.warn("Cotrending test not applicable for Model I.")
            return None
        cv = self.critical_values.get('joint_ct', {}).get(significance_level)
        if cv is None:
            warnings.warn("Critical values not available.")
            return None
        return self.Q_ct <= cv
    
    def summary(self) -> str:
        """
        Generate a formatted summary of test results.
        
        Returns
        -------
        str
            Formatted summary string suitable for publication.
        """
        lines = []
        lines.append("=" * 70)
        lines.append("Carrion-i-Silvestre and Kim (2019) Cointegration Tests")
        lines.append("=" * 70)
        lines.append("")
        
        # Model specification
        model_desc = "Mean shifts" if self.model == 1 else "Linear trend with intercept shifts"
        lines.append(f"Model:                    {self.model} ({model_desc})")
        lines.append(f"Number of breaks:         {self.num_breaks}")
        lines.append(f"Number of regressors:     {self.num_regressors}")
        lines.append(f"Sample size:              {self.sample_size}")
        if self.klags > 0 or self.kleads > 0:
            lines.append(f"DOLS leads/lags:          {self.kleads}/{self.klags}")
        lines.append("")
        
        # Break dates
        if self.break_dates is not None and len(self.break_dates) > 0:
            lines.append("Estimated break dates:")
            for i, (date, frac) in enumerate(zip(self.break_dates, self.break_fractions)):
                lines.append(f"  Break {i+1}: t = {int(date)} (fraction = {frac:.4f})")
            lines.append("")
        
        # Test statistics
        lines.append("-" * 70)
        lines.append("Test Statistics")
        lines.append("-" * 70)
        
        if HAS_TABULATE:
            headers = ["Test", "Statistic", "10%", "5%", "1%", "Decision (5%)"]
            rows = []
            
            # Robust CI test
            cv_r = self.critical_values.get('robust_ci', {})
            decision_r = "CI" if self.is_cointegrated(0.05) else "No CI"
            rows.append([
                "Robust CI (Q_r)",
                f"{self.Q_r:.4f}",
                f"{cv_r.get(0.10, np.nan):.2f}",
                f"{cv_r.get(0.05, np.nan):.2f}",
                f"{cv_r.get(0.01, np.nan):.2f}",
                decision_r
            ])
            
            # Joint CI/CB test
            cv_cb = self.critical_values.get('joint_cb', {})
            decision_cb = "CI+CB" if self.is_cobreaking(0.05) else "Reject"
            rows.append([
                "Joint CI/CB (Q_cb)",
                f"{self.Q_cb:.4f}",
                f"{cv_cb.get(0.10, np.nan):.2f}",
                f"{cv_cb.get(0.05, np.nan):.2f}",
                f"{cv_cb.get(0.01, np.nan):.2f}",
                decision_cb
            ])
            
            # Joint CI/CT test (Model II only)
            if self.model == 2:
                cv_ct = self.critical_values.get('joint_ct', {})
                decision_ct = "CI+CT" if self.is_cotrending(0.05) else "Reject"
                rows.append([
                    "Joint CI/CT (Q_ct)",
                    f"{self.Q_ct:.4f}",
                    f"{cv_ct.get(0.10, np.nan):.2f}",
                    f"{cv_ct.get(0.05, np.nan):.2f}",
                    f"{cv_ct.get(0.01, np.nan):.2f}",
                    decision_ct
                ])
            
            lines.append(tabulate(rows, headers=headers, tablefmt="simple"))
        else:
            lines.append(f"Q_r (Robust CI):      {self.Q_r:.4f}")
            lines.append(f"Q_cb (Joint CI/CB):   {self.Q_cb:.4f}")
            if self.model == 2:
                lines.append(f"Q_ct (Joint CI/CT):   {self.Q_ct:.4f}")
        
        lines.append("")
        lines.append("-" * 70)
        lines.append("Notes:")
        lines.append("- Null hypothesis: Cointegration (and cobreaking/cotrending for joint tests)")
        lines.append("- Reject H0 if test statistic > critical value")
        lines.append("- *** p<0.01, ** p<0.05, * p<0.10")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (
            f"CKTestResults(Q_r={self.Q_r:.4f}, Q_cb={self.Q_cb:.4f}, "
            f"Q_ct={self.Q_ct:.4f}, m={self.num_breaks}, model={self.model})"
        )
    
    def __str__(self) -> str:
        return self.summary()
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary."""
        return {
            'Q_r': self.Q_r,
            'Q_cb': self.Q_cb,
            'Q_ct': self.Q_ct,
            'break_dates': self.break_dates.tolist() if self.break_dates is not None else None,
            'break_fractions': self.break_fractions.tolist() if self.break_fractions is not None else None,
            'model': self.model,
            'num_breaks': self.num_breaks,
            'num_regressors': self.num_regressors,
            'sample_size': self.sample_size,
            'klags': self.klags,
            'kleads': self.kleads,
            'long_run_variance': self.long_run_variance,
            'critical_values': self.critical_values,
        }
    
    def to_latex(self) -> str:
        """
        Generate LaTeX table of results.
        
        Returns
        -------
        str
            LaTeX formatted table.
        """
        lines = []
        lines.append(r"\begin{table}[htbp]")
        lines.append(r"\centering")
        lines.append(r"\caption{Carrion-i-Silvestre and Kim (2019) Cointegration Tests}")
        lines.append(r"\begin{tabular}{lcccc}")
        lines.append(r"\hline\hline")
        lines.append(r"Test & Statistic & 10\% CV & 5\% CV & 1\% CV \\")
        lines.append(r"\hline")
        
        # Robust CI
        cv_r = self.critical_values.get('robust_ci', {})
        sig_r = self._get_significance(self.Q_r, 'robust_ci')
        lines.append(
            f"$Q_r$ (Robust CI) & {self.Q_r:.4f}{sig_r} & "
            f"{cv_r.get(0.10, np.nan):.2f} & {cv_r.get(0.05, np.nan):.2f} & "
            f"{cv_r.get(0.01, np.nan):.2f} \\\\"
        )
        
        # Joint CI/CB
        cv_cb = self.critical_values.get('joint_cb', {})
        sig_cb = self._get_significance(self.Q_cb, 'joint_cb')
        lines.append(
            f"$Q_{{cb}}$ (Joint CI/CB) & {self.Q_cb:.4f}{sig_cb} & "
            f"{cv_cb.get(0.10, np.nan):.2f} & {cv_cb.get(0.05, np.nan):.2f} & "
            f"{cv_cb.get(0.01, np.nan):.2f} \\\\"
        )
        
        # Joint CI/CT (Model II only)
        if self.model == 2:
            cv_ct = self.critical_values.get('joint_ct', {})
            sig_ct = self._get_significance(self.Q_ct, 'joint_ct')
            lines.append(
                f"$Q_{{ct}}$ (Joint CI/CT) & {self.Q_ct:.4f}{sig_ct} & "
                f"{cv_ct.get(0.10, np.nan):.2f} & {cv_ct.get(0.05, np.nan):.2f} & "
                f"{cv_ct.get(0.01, np.nan):.2f} \\\\"
            )
        
        lines.append(r"\hline\hline")
        lines.append(r"\end{tabular}")
        
        # Notes
        lines.append(r"\begin{tablenotes}")
        lines.append(r"\small")
        lines.append(f"\\item Model: {self.model}, Breaks: {self.num_breaks}, "
                    f"Regressors: {self.num_regressors}, T: {self.sample_size}")
        if self.break_fractions is not None and len(self.break_fractions) > 0:
            fracs = ", ".join([f"{f:.2f}" for f in self.break_fractions])
            lines.append(f"\\item Break fractions: {fracs}")
        lines.append(r"\item $^{***}$, $^{**}$, $^{*}$ denote significance at 1\%, 5\%, 10\% levels.")
        lines.append(r"\end{tablenotes}")
        
        lines.append(r"\end{table}")
        
        return "\n".join(lines)


@dataclass
class DmaxTestResults:
    """
    Results container for Dmax cobreaking/cotrending tests.
    
    Attributes
    ----------
    Q_dmax : float
        Dmax test statistic.
    test_type : str
        'dmax_cb' or 'dmax_ct'.
    component_stats : np.ndarray
        Individual test statistics for each m.
    normalized_stats : np.ndarray
        Normalized statistics (Q - a_m) / b_m.
    model : int
        Model specification.
    max_breaks : int
        Maximum number of breaks considered (M).
    num_regressors : int
        Number of stochastic regressors.
    sample_size : int
        Sample size.
    critical_values : dict
        Critical values at different significance levels.
    """
    
    Q_dmax: float
    test_type: str
    component_stats: np.ndarray
    normalized_stats: np.ndarray
    model: int
    max_breaks: int
    num_regressors: int
    sample_size: int
    critical_values: Dict = field(default_factory=dict)
    
    def is_significant(self, significance_level: float = 0.05) -> bool:
        """Test if Dmax statistic is significant."""
        cv = self.critical_values.get(significance_level)
        if cv is None:
            return None
        return self.Q_dmax > cv
    
    def summary(self) -> str:
        """Generate formatted summary."""
        lines = []
        lines.append("=" * 60)
        test_name = "Cobreaking" if self.test_type == 'dmax_cb' else "Cotrending"
        lines.append(f"Dmax {test_name} Test Results")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Model:              {self.model}")
        lines.append(f"Max breaks (M):     {self.max_breaks}")
        lines.append(f"Num regressors:     {self.num_regressors}")
        lines.append(f"Sample size:        {self.sample_size}")
        lines.append("")
        lines.append(f"Q_Dmax statistic:   {self.Q_dmax:.4f}")
        lines.append("")
        lines.append("Critical values:")
        for level, cv in self.critical_values.items():
            lines.append(f"  {int(level*100)}%: {cv:.2f}")
        lines.append("")
        
        sig = self.is_significant(0.05)
        if sig is not None:
            decision = "Reject H0" if sig else "Cannot reject H0"
            lines.append(f"Decision (5%):      {decision}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"DmaxTestResults(Q_dmax={self.Q_dmax:.4f}, type='{self.test_type}')"
    
    def __str__(self) -> str:
        return self.summary()
