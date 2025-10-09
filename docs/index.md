# Quantum Chemistry I/O

[![image](https://img.shields.io/pypi/v/qcio.svg)](https://pypi.python.org/pypi/qcio)
[![image](https://img.shields.io/pypi/l/qcio.svg)](https://pypi.python.org/pypi/qcio)
[![image](https://img.shields.io/pypi/pyversions/qcio.svg)](https://pypi.python.org/pypi/qcio)
[![Actions status](https://github.com/coltonbh/qcio/workflows/Tests/badge.svg)](https://github.com/coltonbh/qcio/actions)
[![Actions status](https://github.com/coltonbh/qcio/workflows/Basic%20Code%20Quality/badge.svg)](https://github.com/coltonbh/qcio/actions)

Elegant and intuitive data structures for quantum chemistry, featuring seamless Jupyter Notebook visualizations.

`qcio` works in harmony with a suite of other quantum chemistry tools for fast, structured, and interoperable quantum chemistry.

## The QC Suite of Programs

- [qcconst](https://github.com/coltonbh/qcconst) - NIST/CODATA2022 core physical constants, conversion factors, and a periodic table with clear source information for every value.
- [qcio](https://github.com/coltonbh/qcio) - Elegant and intuitive data structures for quantum chemistry, featuring seamless Jupyter Notebook visualizations. [Documentation](https://qcio.coltonhicks.com)
- [qccodec](https://github.com/coltonbh/qccodec) - A translation layer between quantum chemistry program inputs and outputs and structured `qcio` objects.
- [qcop](https://github.com/coltonbh/qcop) - A package for operating quantum chemistry programs using `qcio` standardized data structures. Compatible with `TeraChem`, `psi4`, `QChem`, `NWChem`, `ORCA`, `Molpro`, `geomeTRIC` and many more.
- [BigChem](https://github.com/mtzgroup/bigchem) - A distributed application for running quantum chemistry calculations at scale across clusters of computers or the cloud. Bring multi-node scaling to your favorite quantum chemistry program.
- `ChemCloud` - A [web application](https://github.com/mtzgroup/chemcloud-server) and associated [Python client](https://github.com/mtzgroup/chemcloud-client) for exposing a BigChem cluster securely over the internet.

## Installation

For a minimal installation:

```bash
python -m pip install qcio
```

To install all extra feature such as cheminformatics and visualization tools:

```sh
python -m pip install qcio[all]
```

You may need to put `''` around the brackets in some terminals

```sh
python -m pip install 'qcio[all]'
```

## Getting Started

Check out the [API Documentation](./api/overview.md) to understand how qcio works. Take a look at the [Visualizations](./visualizations/overview.md) to see how easy it is to understand your results using qcio!
