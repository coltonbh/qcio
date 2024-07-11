# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [0.10.0] - 2024-07-10

### Added

- A number of additional constant values.
- `constants._SOLVENTS_DIELECTRIC` for a number of common solvents.
- `Structure.from_smiles` to create a 3D structure from a smiles string.

### Changed

- Updated `BOHR_TO_ANGSTROM` from `0.529177210903` to `0.529177210544` in accordance with https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0
- Renamed `Molecule` to `Structure` to better suggest that the coordinates may represent a superstructure comprised of many molecules. Maintained backwards compatibility for passing `ProgramInput(..., molecule=Structure(...))`, and for accessing `prog_input.molecule` with depreciation warnings.
- 🚨 Breaking Change: `OptimizationResults.energies` returns a `np.array` now instead of a `list[float]`. This makes it easier for converting the energies to other units like `kcal/mol`.
- 🚨 Breaking Change: `Identifiers.name_common` renamed to `name` for simplicity.
- 🚨 Breaking Change: Renamed `Structure.identifiers` -> `Structure.ids` to reduce verbosity.
- Made `Identifiers` object directly modifiable so one can add names and smiles to structures easily with `mystruc.ids.name = 'my name'` or `mystruct.ids.smiles = 'CCO'`.

## [0.9.3] - 2024-06-13

### Added

- Registration of all concrete `ProgramOutput[InputType, ResultsType]` on the `outputs.py` module so `pickle` can find the classes for serialization and deserialization within `celery`. The previous approach of registering classes upon instantiation of a class did not work because of multiple processes running in `celery`. The worker process in which the class was instantiated had the class at `outputs.ProgramOutput[...]` however the main process would sometimes need to serialize an object and it would not be in the `outputs.py` module. The former approach appeared to work better than I thought because declaring classes as types for a `trajector` registered them on the `outputs.py` module without my realizing it.

## [0.9.2] - 2024-06-12

### Added

- `precision` argument to `Molecule.save()` method to control the decimal precision of the xyz file output. Default is 17 decimal places to capture all `float64` precision.

### Changed

- Added `GetPydanticSerializer` annotation to `SerializableNDArray` to create the correct json docs for ChemCloud (or any other json schema generator).
- Added `BeforeValidator` to `SerializableNDArray` to coerce all arrays to `float64` for consistency.

## [0.9.1] - 2024-06-11

### Changed

- Changed decimal precision of `Molecule.to_xyz()` string representation of geometry values to 17 decimal places to capture all `float64` precision.

## [0.9.0] - 2024-04-23

### Added

- `Molecule.atomic_numbers` property which uses `qcio.constants.ELEMENTS` to map atomic symbols to atomic numbers.
- Generic `ProgramOutput[InputType, ResultsType]` class to handle all program outputs.

### Removed

**THIS IS A BREAKING RELEASE DUE TO THESE REMOVALS! Trying to maintain core end-user API though.**

- `from_qcel_output` function that is no longer needed since I only need to parse out the results from `QCElemental` objects.
- 🚨 BREAKING CHANGE: `calctype_to_output` since all outputs are now `ProgramOutput` objects parameterized by their input type and results type.
- `test_input_to_output_from_qcel_failed_operation` test since we only parse results from `QCElemental` objects and don't need to parse `FailedOperation` objects.
- `ArrayLike3D` type hint since we are specifically accepting only `NDArray` types for all numpy arrays (instead of previously accepting `List[List[List[float]])` as well) and the dimensionality (shape) cannot be enforced at the type level. All array shapes are enforced by validators and noted as comments.
- Unused `SPReturnType` type hint.

### Changed

- 🚨 BREAKING CHANGE: Inheritance hierarchy for inputs changed to `ProgramInput(FileInput, ...)`, `DualProgramInput(ProgramInput, ...)`. Specifically, all inputs are subclasses of `FileInput` now. So `isinstance(obj, FileInput)` that previously returned `False` for `ProgramInput` and `DualProgramInput` objects (which were not children of `FileInput`) now return True. Update these checks to `if type(obj) is FileInput` to retain the original behavior.
- 🚨 BREAKING CHANGE: While a `ProgramFailure` object is provided for end-user backwards compatibility, because of varying Generics parameters, previous `isinstance(obj, ProgramFailure)` checks that used to return `True` will now return `False`. Check for "equality" to old`ProgramFailure`objects with`if obj.success is False` instead.

## [0.8.2] - 2024-04-09

### Added

- `constants.ELEMENTS` mapping of atomic numbers to element symbols. In anticipation of supporting `xtb` in `qcop` which uses atomic numbers instead of element symbols.

## [0.8.1] - 2024-03-29

### Added

- `py.typed` file to enable type checking in other projects that use `qcio`.

### Changed

- Updated `black`.
- Added `fix_com=True` and `fix_orientation=True` to default conversion from `qcio.Molecule` to `qcelemental.Molecule` objects so that qcel doesn't translate or rotate the molecule unsuspectingly without the user's consent. See default behaviors [here](https://github.com/MolSSI/QCElemental/blob/8e5a8cff52a6438ff9d6c1c6bbf1aeb4f02f12e1/qcelemental/models/molecule.py#L262-L281).
- Renamed `SubProgramArgs` to `SubProgramInput` to be more consistent with the naming convention of the other input objects.

## [0.8.0] - 2024-01-12

### Added

- `OptimizationOutput.save("filename.xyz)` now save the trajectory to an xyz file.

### Fixed

- Saved Molecule xyz files now end with a `\n` character.

## [0.7.1] - 2023-09-27

### Added

- Add validation to `Molecule.symbols` so that all symbols will be capitalized, e.g., `NA` -> `Na`, `h` -> `H`, etc.

### Changed

- `Molecule._to_xyz()` is now a public method `Molecule.to_xyz()` that returns an xyz string rather than writing an xyz file to disk.
- Hoisted `utils.json_dumps` to `qcio.json_dumps` for easier import.

## [0.7.0] - 2023-09-19

### Added

- README.md documentation for basic library utilization.

### Changed

- Renamed `DualProgramArgs` to `SubProgramArgs`.
- Updated `dev-decisions.md` documentation.

## [0.6.1] - 2023-09-08

### Changed

- Removed `.traceback` from `__repr_args__` of `ProgramFailure` so object is more human-readable in an interactive session.

## [0.6.0] - 2023-09-08

### Changed

- Renamed methods `.write_files()` -> `save_files()`, `.add_file()` -> `.open_file()`, `add_files()` -> `.open_files()` to keep a more consistent convention with `.save*` dumping objects to disk and `.open*` opening files on disk.

## [0.5.1] - 2023-09-02

### Added

- `qcio.utils.json_dumps` for serializing `pydantic` objects or lists of objects. Helpful for serializing requests to send of HTTP.
- `typos` pre-commit check.
- `@classmethod` decorator to `@field_validator` functions as per [pydantic docs](https://docs.pydantic.dev/latest/usage/validators/#field-validators).
- `SinglePointResults.scf_dipole_moment`.

### Fixed

- Removed invalid objects in `qcio.__init__.py.__all__`.

### Changed

- `model.save()` now saves json with `indent=4` by default.

## [0.5.0] - 2023-08-31

### Changed

- Updated `pydantic` from `v1` -> `v2`.

## [0.4.2] - 2023-08-18

### Added

- `DualProgramArgs` object.

## [0.4.1] - 2023-07-20

### Fixed

- `final_molecule` lookup now returns `None` if `.trajectory` is empty rather than raising `IndexError`.

## [0.4.0] - 2023-07-19

### Changed

- Changed `Provenance.working_dir` -> `scratch_dir`.

## [0.3.5] - 2023-07-18

### Changed

- Dropped `.energies` and `.molecules` on `OptimizationResult` in favor of `@property` lookups on the `.trajectory` attribute. If memory utilization really becomes an issue consider optimizing in future by creating attributes of `.energy` or `.molecules` with smaller memory footprint.

## [0.3.4] - 2023-07-18

### Changed

- Dropped `results.py` file and moved all results objects to `outputs.py` to remove circular dependency.

## [0.3.3] - 2023-07-17

### Fixed

- Fixed `SinglePointResult.normal_modes_cartesian` to be proper 3D structure with xyz displacements for each atom for each normal mode.

### Changed

- `from_qcel_output` now overwrites the core results value with `.return_result` since `QCElemental` does not always write energy/gradient/hessian values to `AtomicResult.properties`.

## [0.3.2] - 2023-07-17

### Fixed

- `Molecule.dict()` raised exception if `.connectivity` did not exist since `super().dict()` removes empty collections for serialization.

## [0.3.1] - 2023-07-17

### Added

- `Molecule.connectivity` for `rdkit` and other MM package support that depends on explicitly defined bonds.

## [0.3.0] - 2023-07-17

### Changed

- Dropped `.program_args` nesting from input objects in favor of a flatter model structure. This makes defining inputs much quick/easier.
- Renamed `calc_type` -> `calctype`.
- Change computational model to use `ProgramInput` and `DualProgramInput` instead of `SinglePointInput` and `OptimizationInput` to enable more flexibility in the future.
- Added frequency analysis values to `SinglePointResults` object.

## [0.2.1] - 2023-06-29

### Fixed

- Removed mistaken call to `print()` leftover from debugging.

## [0.2.0] - 2023-06-29

### Added

- `wall_time`, `hostcpus`, `hostname`, `hostmem` to `Provenance`
- `pstdout` and `ptraceback` as aliased attributes on `Output` and `FailedOutput` to quickly print out the values for easier viewing.
- `Molecule.formula` property to return Hill System molecular formula.
- Serialization support for `yaml` and `toml` in `.save()` and `.open()` methods.
- Compatibility for `QCElemental`. `SinglePointInput` objects can now run `.to_qcel()` to return a `dict` representation of an `AtomicInput` and `.to_output_from_qcel` to convert a `dict` representation of an `AtomicResult` or `FailedOperation` to a `SinglePointSuccessfulOutput` or `SinglePointFailedOutput` object.

### Changed

- Changed `Provenance.working_dir` from `str` -> `Path`

## [0.1.0] - 2023-06-28

### Added

- Core models for Single Point calculations:
  - `FileArgs`
  - `FileInput`
  - `FileSuccessfulOutput`
  - `FileFailedOutput`
  - `Provenance`
  - `Model`
  - `SPCalcType`
  - `SinglePointProgramArgs`
  - `SinglePointInput`
  - `SinglePointSuccessfulOutput`
  - `SinglePointFailedOutput`
  - `SinglePointComputedProperties`
  - `Wavefunction`

[unreleased]: https://github.com/coltonbh/qcio/compare/0.10.0...HEAD
[0.10.0]: https://github.com/coltonbh/qcio/releases/tag/0.10.0
[0.9.3]: https://github.com/coltonbh/qcio/releases/tag/0.9.3
[0.9.2]: https://github.com/coltonbh/qcio/releases/tag/0.9.2
[0.9.1]: https://github.com/coltonbh/qcio/releases/tag/0.9.1
[0.9.0]: https://github.com/coltonbh/qcio/releases/tag/0.9.0
[0.8.2]: https://github.com/coltonbh/qcio/releases/tag/0.8.2
[0.8.1]: https://github.com/coltonbh/qcio/releases/tag/0.8.1
[0.8.0]: https://github.com/coltonbh/qcio/releases/tag/0.8.0
[0.7.1]: https://github.com/coltonbh/qcio/releases/tag/0.7.1
[0.7.0]: https://github.com/coltonbh/qcio/releases/tag/0.7.0
[0.6.1]: https://github.com/coltonbh/qcio/releases/tag/0.6.1
[0.6.0]: https://github.com/coltonbh/qcio/releases/tag/0.6.0
[0.5.1]: https://github.com/coltonbh/qcio/releases/tag/0.5.1
[0.5.0]: https://github.com/coltonbh/qcio/releases/tag/0.5.0
[0.4.2]: https://github.com/coltonbh/qcio/releases/tag/0.4.2
[0.4.1]: https://github.com/coltonbh/qcio/releases/tag/0.4.1
[0.4.0]: https://github.com/coltonbh/qcio/releases/tag/0.4.0
[0.3.5]: https://github.com/coltonbh/qcio/releases/tag/0.3.5
[0.3.4]: https://github.com/coltonbh/qcio/releases/tag/0.3.4
[0.3.3]: https://github.com/coltonbh/qcio/releases/tag/0.3.3
[0.3.2]: https://github.com/coltonbh/qcio/releases/tag/0.3.2
[0.3.1]: https://github.com/coltonbh/qcio/releases/tag/0.3.1
[0.3.0]: https://github.com/coltonbh/qcio/releases/tag/0.3.0
[0.2.1]: https://github.com/coltonbh/qcio/releases/tag/0.2.1
[0.2.0]: https://github.com/coltonbh/qcio/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcio/releases/tag/0.1.0
