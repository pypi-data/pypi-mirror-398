# MCGT: Model of Gravitational Time Curvature

[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Official repository for the MCGT research project, focused on Gravitational Wave Phase Analysis and Cosmological Invariants.

## 🚀 Key Features
- **Sobol 8D Sampling**: Production-grade parameter space exploration.
- **Reproducible Pipeline**: All chapters certified with SHA256 consistency checks.
- **Physics Modules**: From CMB spectra to GW phase residuals.

## 🛠 Installation
```bash
git clone https://github.com/JeanPhilipLalumiere/MCGT.git
pip install -r requirements.txt
```

## 📊 Verification
```bash
python zz-manifests/diag_consistency.py zz-manifests/manifest_master.json
```

*For French version, see [README_fr.md](README_fr.md).*
