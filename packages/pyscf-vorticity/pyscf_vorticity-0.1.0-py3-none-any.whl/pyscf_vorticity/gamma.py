"""
pyscf_vorticity/gamma.py
γ extraction utilities
"""

import numpy as np

def extract_gamma(n_electrons, alphas, method='log'):
    """
    Extract correlation dimension γ from α scaling
    
    α ∝ N^(-γ)  →  log(α) = -γ log(N) + const
    
    Parameters
    ----------
    n_electrons : array-like
        Number of electrons for each system
    alphas : array-like
        Coupling constants (E_xc / V)
    method : str
        'log' for log-log fit (default)
    
    Returns
    -------
    gamma : float
        Correlation dimension
    r_squared : float
        Coefficient of determination
    a_optimal : float
        Optimal exact exchange mixing: a = 1/(1+γ)
    """
    n_arr = np.array(n_electrons)
    a_arr = np.array(alphas)
    
    # Filter valid values
    valid = (a_arr > 1e-14) & (n_arr > 0)
    if np.sum(valid) < 2:
        return 0.0, 0.0, 0.5
    
    log_n = np.log(n_arr[valid])
    log_a = np.log(a_arr[valid])
    
    # Linear fit: log(α) = -γ log(N) + const
    coeffs = np.polyfit(log_n, log_a, 1)
    gamma = -coeffs[0]
    
    # R²
    pred = np.polyval(coeffs, log_n)
    ss_res = np.sum((log_a - pred)**2)
    ss_tot = np.sum((log_a - log_a.mean())**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    # Optimal exact exchange
    a_optimal = 1 / (1 + gamma) if gamma > -1 else 0.5
    
    return gamma, r_squared, a_optimal


def compute_alpha(E_corr, V):
    """
    Compute coupling constant α = |E_corr| / V
    
    Parameters
    ----------
    E_corr : float
        Correlation energy (E_FCI - E_HF)
    V : float
        Vorticity
    
    Returns
    -------
    alpha : float
        Coupling constant
    """
    if V < 1e-14:
        return 0.0
    return abs(E_corr) / V
