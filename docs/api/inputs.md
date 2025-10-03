Input structures for specifying quantum chemistry calculations. The most commonly used structure is a `ProgramInput` which tells a single program how to run a calculation.

A `DualProgramInput` is used when two programs are used in conjunction for an operation. For example, doing a geometry optimization with `geomeTRIC` while using a `subprogram` like `TeraChem` or `Psi4` to compute the gradients.

A `FileInput` is an escape hatch that allows you to run _any_ calculation in any QC program (or any program for that matter), even if it isn't a supported [`CalcType`](./calctype.md) in `qcio` yet. You can use a `FileInput` to store the native input files (text and binary) for a QC program along with the relevant command line args for a calculation. Using [qcop](https://github.com/coltonbh/qcop) you can submit a `FileInput` a QC program and all output files and `stdout` produced by that program will be collected and returned in a user-friendly `Results` object. `FileInput` allows you to continue to use `qcio` even for calculations that haven't yet been standardized.

  
::: qcio.Inputs

::: qcio.ProgramInput
    options:
        inherited_members: true
        members: 
            - add_file 
            - add_files 
            - save_files

::: qcio.DualProgramInput
    options:
        inherited_members: true
        members: 
            - add_file 
            - add_files 
            - save_files 

::: qcio.FileInput
    options:
        inherited_members: true
        members: 
        - add_file 
        - add_files 
        - save_files 
        - from_directory

::: qcio.ProgramArgs
    options:
        inherited_members: true
        members: 
        - add_file 
        - add_files 
        - save_files
