# Geoloop: A BHE Calculator for Python

[![PyPI](https://img.shields.io/pypi/v/geoloop.svg)](https://pypi.org/project/geoloop/)
[![Documentation](https://img.shields.io/badge/docs-latest-blue)](https://geoloop-8f7a36.ci.tno.nl/)

## What is **Geoloop**?

**Geoloop** is a Python package for simulating borehole heat exchanger (BHE) systems,
with a focus on optimal implementation of subsurface thermal properties and their impact on system performance.

**Geoloop** incorporates (uncertainty in) depth-variations in subsurface thermal conductivity, subsurface temperature, 
BHE design and diverse operational boundary conditions such as seasonal load variations or 
minimum fluid temperatures, in a tool for deterministic or stochastic performance analyses with the opportunity
for optimization of the system design and operation. This makes Geoloop ideal for scenario analyses and sensitivity 
studies in both research and practical applications.

**Geoloop** uses thermal response factors (*g*-functions) calculated using the analytical Finite Line Source model from 
the *pygfunction* package. This setup is extended into a stacked approach for depth-dependent thermal response calculations. 
A detailed description and benchmark of this depth-dependent semi-analytical method is provided in Korevaar & Van Wees (in prep.).
**Geoloop's** generic framework allows for easy switching between simulation methods, including the innovative depth-dependent
semi-analytical approach, the depth-uniform implementation of g-functions as implemented in *pygfunction* and a numerical 
finite volume approach.

---

## Installation

Install from PyPI using:

```bash
pip install geoloop
```

For detailed setup instructions (including uv-based environments and development setup),
see the [Installation Guide](https://geoloop-8f7a36.ci.tno.nl/installation/install/).

---

## Requirements

Geoloop requires **Python 3.12 or higher**.

Core dependencies include:
- pygfunction
- matplotlib
- numpy
- scipy
- h5py
- xarray
- pandas
- seaborn
- tqdm
- netCDF4
- SecondaryCoolantProps
- openpyxl
- h5netcdf
- pathlib
- pydantic
- typer

---

## Quick Start

Explore the [Examples](docs/examples/) folder to get started quickly with Geoloop.

Read the full documenation [here](https://geoloop-8f7a36.ci.tno.nl/).

---

## License

This project is licensed under the Apache 2.0 License.  
See the [LICENSE.md](LICENSE.md) file for details.

---

## Acknowledgments

Developed with the support of the Dutch funding agency **RVO**, in a consortium project with grant nr. MOOI322009.

---


