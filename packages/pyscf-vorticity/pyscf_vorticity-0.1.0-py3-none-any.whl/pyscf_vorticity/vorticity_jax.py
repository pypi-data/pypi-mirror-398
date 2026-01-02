"""
pyscf_vorticity/vorticity_jax.py
JAX-accelerated vorticity calculation
"""

import jax.numpy as jnp
from jax import jit
import numpy as np

def compute_vorticity(rdm2, n_orb, svd_cut=0.95):
    """
    Compute vorticity from 2-RDM (JAX version)
    
    Note: k selection done in NumPy, matrix ops in JAX
    """
    # Reshape to matrix
    M = jnp.array(rdm2.reshape(n_orb**2, n_orb**2))
    
    # SVD (JAX)
    U, S, Vt = jnp.linalg.svd(M, full_matrices=False)
    
    # Dynamic k selection (NumPy - outside JIT)
    S_np = np.array(S)
    total_var = np.sum(S_np**2)
    if total_var < 1e-14:
        return 0.0, 0
    
    cumvar = np.cumsum(S_np**2) / total_var
    k = int(np.searchsorted(cumvar, svd_cut) + 1)
    k = max(k, 2)
    k = min(k, len(S_np))
    
    # Λ-space projection (JAX with static k)
    S_proj = U[:, :k]
    M_lambda = S_proj.T @ M @ S_proj
    
    # Gradient
    grad_M = jnp.zeros_like(M_lambda)
    grad_M = grad_M.at[:-1, :].set(M_lambda[1:, :] - M_lambda[:-1, :])
    
    # Current: J = M_λ @ ∇M_λ
    J_lambda = M_lambda @ grad_M
    
    # Vorticity: ||J - J^T||²
    curl_J = J_lambda - J_lambda.T
    V = jnp.sum(curl_J**2)
    
    return float(jnp.sqrt(V)), k


# Optional: JIT-compiled core for repeated calls with same k
def _compute_vorticity_core(M, U, k):
    """JIT-compilable core (fixed k)"""
    S_proj = U[:, :k]
    M_lambda = S_proj.T @ M @ S_proj
    
    grad_M = jnp.zeros_like(M_lambda)
    grad_M = grad_M.at[:-1, :].set(M_lambda[1:, :] - M_lambda[:-1, :])
    
    J_lambda = M_lambda @ grad_M
    curl_J = J_lambda - J_lambda.T
    
    return jnp.sqrt(jnp.sum(curl_J**2))
