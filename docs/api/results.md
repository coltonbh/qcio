# Results

`Results` is the core object that captures all information from a QC calculation including all input data, the computed values and files (collectively called [`Data`](#data)), and additional metadata such as `logs` and [`Provenance`](./provenance.md) information. The `.data` attribute will correspond to the [`CalcType`](./calctype.md) requested, e.g., a [`SinglePointData`](#qcio.SinglePointData), [`OptimizationsData`](#qcio.OptimizationData), etc.

::: qcio.Results
options:
members: false

## Data

::: qcio.Data

::: qcio.SinglePointData
options:
members: false

::: qcio.OptimizationData
options:
members: - structures - final_structure - energies - final_energy - to_xyz - save

::: qcio.ConformerSearchData

::: qcio.Wavefunction
