# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [0.3.4]

### Changed

- Dropped `results.py` file and moved all results objects to `outputs.py` to remove circular dependency.

## [0.3.3]

### Fixed

- Fixed `SinglePointResult.normal_modes_cartesian` to be proper 3D structure with xyz displacements for each atom for each normal mode.

### Changed

- `from_qcel_output` now overwrites the core results value with `.return_result` since `QCElemental` does not always write energy/gradient/hessian values to `AtomicResult.properties`.

## [0.3.2]

### Fixed

- `Molecule.dict()` raised exception if `.connectivity` did not exist since `super().dict()` removes empty collections for serialization.

## [0.3.1]

### Added

- `Molecule.connectivity` for `rdkit` and other MM package support that depends on explicitly defined bonds.

## [0.3.0]

### Changed

- Dropped `.program_args` nesting from input objects in favor of a flatter model structure. This makes defining inputs much quick/easier.
- Renamed `calc_type` -> `calctype`.
- Change computational model to use `ProgramInput` and `DualProgramInput` instead of `SinglePointInput` and `OptimizationInput` to enable more flexibility in the future.
- Added frequency analysis values to `SinglePointResults` object.

## [0.2.1]

### Fixed

- Removed mistaken call to `print()` leftover from debugging.

## [0.2.0]

### Added

- `wall_time`, `hostcpus`, `hostname`, `hostmem` to `Provenance`
- `pstdout` and `ptraceback` as aliased attributes on `Output` and `FailedOutput` to quickly print out the values for easier viewing.
- `Molecule.formula` property to return Hill System molecular formula.
- Serialization support for `yaml` and `toml` in `.save()` and `.open()` methods.
- Compatibility for `QCElemental`. `SinglePointInput` objects can now run `.to_qcel()` to return a `dict` representation of an `AtomicInput` and `.to_output_from_qcel` to convert a `dict` representation of an `AtomicResult` or `FailedOperation` to a `SinglePointSuccessfulOutput` or `SinglePointFailedOutput` object.

### Changed

- Changed `Provenance.working_dir` from `str` -> `Path`

## [0.1.0]

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

[unreleased]: https://github.com/coltonbh/qcio/compare/0.3.4...HEAD
[0.3.4]: https://github.com/coltonbh/qcio/releases/tag/0.3.4
[0.3.3]: https://github.com/coltonbh/qcio/releases/tag/0.3.3
[0.3.2]: https://github.com/coltonbh/qcio/releases/tag/0.3.2
[0.3.1]: https://github.com/coltonbh/qcio/releases/tag/0.3.1
[0.3.0]: https://github.com/coltonbh/qcio/releases/tag/0.3.0
[0.2.1]: https://github.com/coltonbh/qcio/releases/tag/0.2.1
[0.2.0]: https://github.com/coltonbh/qcio/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcio/releases/tag/0.1.0
