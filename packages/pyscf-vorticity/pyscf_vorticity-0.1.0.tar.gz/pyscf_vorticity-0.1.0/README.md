# pyscf-vorticity

Geometric correlation analysis for quantum chemistry

## What it does

Computes an **effective** correlation dimension γ from first-principles
two-particle reduced density matrices, helping you select the optimal
DFT functional for your system.

---

## Quick Start
```python
from pyscf import gto, scf, fci
from pyscf_vorticity import compute_vorticity

# Your molecule
mol = gto.M(atom='...', basis='cc-pvdz')
mf = scf.RHF(mol).run()
cisolver = fci.FCI(mf)
E_fci, fcivec = cisolver.kernel()

# Compute vorticity
rdm2 = cisolver.make_rdm12(fcivec, mol.nao, nelec)[1]
V, k = compute_vorticity(rdm2, mol.nao)
alpha = abs(E_fci - mf.e_tot) / V

# → Use γ to guide functional selection
```

---

## HOW TO: Choosing Your Functional

The following table provides **practical guidelines** based on 
physical interpretation of γ. These are recommendations, 
not absolute rules.

| Your γ | Optimal a | Recommended Functional |
|--------|-----------|------------------------|
| γ ≈ 0 | a ≈ 1.0 | HF or high exact exchange hybrid |
| γ ≈ 1 | a ≈ 0.5 | M06-2X, BH&HLYP |
| γ ≈ 2 | a ≈ 0.33 | PBE0, B3LYP |
| γ ≈ 3-4 | a ≈ 0.25 | B3LYP |
| γ > 5 | a < 0.15 | TPSSh, pure GGA |

**Guideline formula:** `a ≈ 1 / (1 + γ)`

---

## WHY: The Physics Behind It

### The Problem

Standard DFT functionals contain empirical "magic numbers" - 
like B3LYP's 20% exact exchange - that work **on average** 
but fail systematically for:
- **Strong correlation** (Mott insulators, transition metals)
- **Static correlation** (bond breaking, diradicals)
- **Weak correlation** (metals)

### The Root Cause

Most functionals implicitly assume a **fixed** correlation structure.

Reality: correlation strength **varies** across systems.

### The Solution

The exchange-correlation energy scales with a vorticity measure V,
allowing extraction of the correlation exponent γ through 
system-size dependence.

**γ characterizes how correlated your system is:**

| γ value | Correlation type | Electron behavior |
|---------|------------------|-------------------|
| γ → 0 | Strong (Mott) | Localized, atomic-like |
| γ ≈ 1 | Intermediate | Partially localized |
| γ ≈ 2 | Moderate | Molecular bonding |
| γ > 3 | Weak (metallic) | Fully delocalized |

---

## HOW TO: Strong Correlation Systems

When γ → 0, standard DFT typically fails.

**What to do:**

1. **Use high exact exchange**
```python
   mf = dft.RKS(mol)
   mf.xc = 'HF*0.5 + PBE*0.5'  # 50% exact exchange
```

2. **Consider range-separated hybrids**
```python
   mf.xc = 'camb3lyp'
```

3. **Or go beyond DFT** (CASSCF, DMFT, CC)

**WHY this works:**

Strong correlation (γ → 0) indicates **localized** electrons.
Localized electrons require exact exchange to avoid self-interaction error.
GGA/LDA assume delocalized electrons → systematic failure.

---

## HOW TO: Weak Correlation (Metals)

When γ > 3:
```python
mf.xc = 'PBE'   # Pure GGA
mf.xc = 'TPSS'  # Meta-GGA
```

**WHY:**

Delocalized electrons screen effectively.
Exact exchange over-localizes → wrong band structure.

---

## Validated Examples

### H₂ Dissociation
```
R = 0.74Å: α = 0.062 (equilibrium)
R = 1.50Å: α = 0.039 (minimum)
R = 5.00Å: α = 0.097 (dissociated)
```

U-shaped α(R) captures weak → strong correlation transition.

### Atoms
```
He (2e):  α = 0.090
Be (4e):  α = 0.003
Ne (10e): α = 0.004
```

The 30× drop from 2e to 4+e systems ("α-cliff") 
reflects the emergence of many-body correlation structure.

---

## Installation
```bash
pip install git+https://github.com/miosync-masa/pyscf-vorticity.git
```

GPU acceleration (recommended):
```bash
pip install jax jaxlib
```

---

## Citation
```bibtex
@article{iizumi2025geometric,
  title={Geometric Origin of Exchange-Correlation in Density Functional Theory},
  author={Iizumi, Masamichi},
  journal={arXiv preprint},
  year={2025}
}
```

---

## License

MIT
