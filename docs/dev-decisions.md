# Development Decisions

## K.I.S.S. Stuff

- All units are Atomic Units (AU). E.g., this means geometries in `Molecule` are defined in `Bohr`.
- All container objects that may be empty (e.g. dicts, lists, sets, etc) will be set to an empty object by default rather than `Optional[container] = None`. This makes accessing the attributes for end users more routine because they can run `obj.extras.get()` without having to do `if obj.extras is not None` check first. Or `len(obj.some_list)` while avoiding `not None` checks.

## Road Map

- Deal with `pubchem` data API later. There are a few packages on `pypi` that do this. `qcel` has its own interface as well. I think I only need a very basic lookup so I'll probably just do it myself inside one `@classmethod` on `Molecule`

## Design Decisions

- What should be part of the input object and would should be parameters passed to some `compute` function (in `qcop`) that controls the execution of the program?
  - Anything that doesn't directly control the qc program--like parameters and options for `qcop`--shouldn't be part of the input data structure. Rather it should be thought of as control parameters for the executing wrapper (`qcop`). E.g., to collect stdout or not should not be an "input" dat field, that is a question of whether `qcop` collects and returns stdout, it's not an "input" to the program.
- Where to place `program`?
  - Should it be in the input data? No. Does a TeraChem input file have the program `terachem` stated in it? No. Running TeraChem is a command line argument specified at runtime, not a data input. Therefore it belongs as an argument to `.compute()` in `qcop`.
- `Files` is really the parent class of an `Input`. An `Input` is an extraction from generic input files of various unstructured values and the placing of those values into structured format. Think of all structured objects as choices about what new values to pull out from native file formats into a more generalized and structured representation of the data.

## Publishing Checklist

- Update `CHANGELOG.md`
- Bump version in `pyproject.toml`
- Tag commit with a version and GitHub Actions will publish it to pypi if tag is on `master` branch.
- `git push`
- `git push --tags`
