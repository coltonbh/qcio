# Outputs

`ProgramOutput` is the core object that captures all information from a QC calculation including all input data, the computed values and files (collectively called [`Results`](#results)), and additional metadata such as `stdout` and [`Provenance`](./provenance.md) information. The `.results` attribute will correspond to the [`CalcType`](./calctype.md) requested, e.g., a [`SinglePointResults`](#qcio.SinglePointResults), [`OptimizationsResults`](#qcio.OptimizationResults), etc.

::: qcio.ProgramOutput
    options:
        members: false

## Results

::: qcio.Results

::: qcio.SinglePointResults
    options:
        members: false

::: qcio.OptimizationResults
    options:
        members:
            - structures
            - final_structure
            - energies
            - final_energy
            - to_xyz
            - save
::: qcio.Wavefunction

