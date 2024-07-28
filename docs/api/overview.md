# Overview

## 🧠 `qcio` operates on a simple mental model

- [`Structure`](./structure.md) objects represent a collection of atoms, a molecule, or any super molecular structure in 3D cartesian space.
- [`Input`](./inputs.md) objects define the input parameters for a calculation.
- [`ProgramOutput`](./outputs.md) objects store computed values and output files (collectively called [`Results`](./outputs.md#qcio.Results)) from a calculation. They also store the exact input data (`.input_data`) used generated them, relevant metadata, and [`Provenance`](./provenance.md) information so you have full visibility of how every result was generated.
- Other objects, such as [`Identifiers`](./structure.md), [`Files`](./files.md), [`Provenance`](./provenance.md), and [`Model`](./model.md) support these core data structures by organizing relevant information in a user-friendly way.
- 💾 Saving your data to disk and re-opening it again later for analysis is as simple as calling [`my_obj.save(/path/to/file.json)`](./qciomodelbase.md#qcio.models.base_models.QCIOModelBase.save) or [`MyModel.open(/path/to/file.json)`](./qciomodelbase.md#qcio.models.base_models.QCIOModelBase.open). These methods are not shown in the documentation for individual classes to avoid redundancy. Files can be saved as `.json`, `.yaml`, or `.toml`. `Structure` and `OptimizationResults` (which contains a list of `Structures`) may additionally be saved as `.xyz` files for compatibility with external program.
