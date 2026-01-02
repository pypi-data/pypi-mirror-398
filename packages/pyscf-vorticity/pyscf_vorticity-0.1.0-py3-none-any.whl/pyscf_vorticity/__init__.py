"""
pyscf-vorticity: Geometric correlation analysis
"""

#Backend
try:
    import jax
    import jax.numpy as jnp
    from .vorticity_jax import compute_vorticity
    BACKEND = 'jax'
    
    # GPU check
    try:
        devices = jax.devices('gpu')
        if devices:
            DEVICE = 'gpu'
        else:
            DEVICE = 'cpu'
    except:
        DEVICE = 'cpu'
        
except ImportError:
    from .vorticity_numpy import compute_vorticity
    BACKEND = 'numpy'
    DEVICE = 'cpu'

print(f"pyscf-vorticity: backend={BACKEND}, device={DEVICE}")

# Public API
from .gamma import extract_gamma

__version__ = '0.1.0'
__all__ = ['compute_vorticity', 'extract_gamma', 'BACKEND', 'DEVICE']
