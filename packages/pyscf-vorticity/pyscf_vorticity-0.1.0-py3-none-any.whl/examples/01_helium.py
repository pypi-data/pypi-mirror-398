"""
Example 1: Helium atom
======================

Simplest test case for pyscf-vorticity
"""

from pyscf import gto, scf, fci
from pyscf_vorticity import compute_vorticity

# Build He atom
mol = gto.M(atom='He 0 0 0', basis='cc-pvdz')
print(f"Helium atom: {mol.nelectron} electrons, {mol.nao} orbitals")

# RHF
mf = scf.RHF(mol).run(verbose=0)
print(f"E(HF) = {mf.e_tot:.6f} Ha")

# FCI (exact for 2 electrons)
cisolver = fci.FCI(mf)
E_fci, fcivec = cisolver.kernel()
print(f"E(FCI) = {E_fci:.6f} Ha")

# Correlation energy
E_corr = E_fci - mf.e_tot
print(f"E_corr = {E_corr:.6f} Ha = {E_corr*27.211:.3f} eV")

# Compute vorticity
n_orb = mol.nao
n_elec = mol.nelectron
rdm1, rdm2 = cisolver.make_rdm12(fcivec, n_orb, (n_elec//2, n_elec//2))

V, k = compute_vorticity(rdm2, n_orb)
alpha = abs(E_corr) / V

print(f"\nResults:")
print(f"  V = {V:.4f}")
print(f"  k = {k}")
print(f"  α = {alpha:.4f}")
print(f"\nExpected: V ≈ 0.361, α ≈ 0.090")
