"""
Unit tests for pyscf-vorticity
"""

import numpy as np
import pytest

# Skip if pyscf not available
pyscf = pytest.importorskip("pyscf")

from pyscf import gto, scf, fci
from pyscf_vorticity import compute_vorticity


def test_helium():
    """Test He atom gives expected vorticity"""
    mol = gto.M(atom='He 0 0 0', basis='cc-pvdz')
    mf = scf.RHF(mol).run(verbose=0)
    cisolver = fci.FCI(mf)
    E_fci, fcivec = cisolver.kernel()
    
    n_orb = mol.nao
    rdm1, rdm2 = cisolver.make_rdm12(fcivec, n_orb, (1, 1))
    V, k = compute_vorticity(rdm2, n_orb)
    
    assert abs(V - 0.361) < 0.01, f"V = {V}, expected ~0.361"
    assert k == 2, f"k = {k}, expected 2"


def test_h2_equilibrium():
    """Test H2 at equilibrium"""
    mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='cc-pvdz', unit='angstrom')
    mf = scf.RHF(mol).run(verbose=0)
    cisolver = fci.FCI(mf)
    E_fci, fcivec = cisolver.kernel()
    
    rdm1, rdm2 = cisolver.make_rdm12(fcivec, mol.nao, (1, 1))
    V, k = compute_vorticity(rdm2, mol.nao)
    
    assert abs(V - 0.557) < 0.01, f"V = {V}, expected ~0.557"


def test_h2_dissociation_trend():
    """Test that α shows U-shape during dissociation"""
    alphas = []
    
    for R in [0.74, 1.5, 5.0]:
        mol = gto.M(atom=f'H 0 0 0; H 0 0 {R}', basis='cc-pvdz', unit='angstrom')
        mf = scf.RHF(mol).run(verbose=0)
        cisolver = fci.FCI(mf)
        E_fci, fcivec = cisolver.kernel()
        
        rdm1, rdm2 = cisolver.make_rdm12(fcivec, mol.nao, (1, 1))
        V, k = compute_vorticity(rdm2, mol.nao)
        E_corr = E_fci - mf.e_tot
        alpha = abs(E_corr) / V
        alphas.append(alpha)
    
    # U-shape: α(1.5) < α(0.74) and α(1.5) < α(5.0)
    assert alphas[1] < alphas[0], "α should decrease from equilibrium"
    assert alphas[1] < alphas[2], "α should increase toward dissociation"


def test_vorticity_positive():
    """Vorticity should always be positive"""
    mol = gto.M(atom='He 0 0 0', basis='sto-3g')
    mf = scf.RHF(mol).run(verbose=0)
    cisolver = fci.FCI(mf)
    E_fci, fcivec = cisolver.kernel()
    
    rdm1, rdm2 = cisolver.make_rdm12(fcivec, mol.nao, (1, 1))
    V, k = compute_vorticity(rdm2, mol.nao)
    
    assert V >= 0, "Vorticity must be non-negative"
