# Development Decisions

## K.I.S.S. Stuff

- In keeping with [pydantic-v2](https://docs.pydantic.dev/blog/pydantic-v2/) I will just support `.json` for now to keep things maximally simple. I don't see any reason to support more formats at this time.
- All units are Atomic Units (AU). E.g., this means geometries in `Molecule` are defined in `Bohr`.
- All container objects that may be empty (e.g., `keywords`)--dicts, lists, sets, etc.--will be set to an empty object by default rather than `Optional[container] = None`. This makes accessing the attributes for end users more routine because they can run `obj.extras.get()` without having to do `if obj.extras is not None` check first. Or `len(obj.some_list)` while avoiding `not None` checks.

## Road Map

- Deal with `pubchem` data API later. There are a few packages on `pypi` that do this. `qcel` has its own interface as well. I think I only need a very basic lookup so I'll probably just do it myself inside one `@classmethod` on `Molecule`

## Design Decisions

- What should be part of the input `Specification` and would should be parameters passed to some `compute` function that controls the execution of the program?
  - Anything that doesn't directly control the program--like keywords or other settings for the external program--shouldn't be passes as part of the input data. Rather it should be thought of as control parameters for the executing wrapper (`qcop`). E.g., to collect stdout or not should not be an "input" field, that is a question of whether `qcopt` collects and returns stdout, it's not an "input" to the program.
- Where to place `program`?
  - Should it be part of the `Specification`?
- `Files` is really the parent class of `Specification`. A `Specification` is an extraction from generic input files of various unstructured values and the placing of those values into structured format.
  - So it could make sense to have `FileInput` have a `.specification` but then I have doubly nested the only object that matters, `Files`, at `FileInput.specification.files` rather than just using the `Files` object directly as a way to maintain a design pattern. I think for now it's better to just keep it flat and allow using `Files` as an input object to `compute`.
- Maybe rename `Specification` to something more helpful. It is technically the program inputs.

## Publishing Checklist

- Update `CHANGELOG.md`
- Bump version in `pyproject.toml`
- Tag commit with a version and GitHub Actions will publish it to pypi if tag is on `master` branch.
- `git push`
- `git push --tags`
