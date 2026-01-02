"""
NumPy fallback (CPU only)
"""

import numpy as np
from scipy.linalg import svd

def compute_vorticity(rdm2, n_orb, svd_cut=0.95):
    """
    Compute vorticity from 2-RDM (NumPy version)
    
    Fallback for systems without JAX
    """
    M = rdm2.reshape(n_orb**2, n_orb**2)
    
    U, S, Vt = svd(M, full_matrices=False)
    
    total_var = np.sum(S**2)
    if total_var < 1e-14:
        return 0.0, 0
    
    cumvar = np.cumsum(S**2) / total_var
    k = np.searchsorted(cumvar, svd_cut) + 1
    k = max(k, 2)
    k = min(k, len(S))
    
    S_proj = U[:, :k]
    M_lambda = S_proj.T @ M @ S_proj
    
    grad_M = np.zeros_like(M_lambda)
    grad_M[:-1, :] = M_lambda[1:, :] - M_lambda[:-1, :]
    
    J_lambda = M_lambda @ grad_M
    curl_J = J_lambda - J_lambda.T
    V = np.sum(curl_J**2)
    
    return np.sqrt(V), k
