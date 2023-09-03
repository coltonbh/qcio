# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

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

[unreleased]: https://github.com/coltonbh/qcio/compare/0.5.1...HEAD
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
