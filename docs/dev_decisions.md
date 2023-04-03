# Development Decisions

## K.I.S.S. Stuff

- In keeping with [pydantic-v2](https://docs.pydantic.dev/blog/pydantic-v2/) I will just support `.json` for now to keep things maximally simple. I don't see any reason to support more formats at this time.
- All units are Atomic Units (AU). E.g., this means geometries in `Molecule` are defined in `Bohr`.

## Road Map

- Deal with `pubchem` data API later. There are a few packages on `pypi` that do this. `qcel` has its own interface as well. I think I only need a very basic lookup so I'll probably just do it myself inside one `@classmethod` on `Molecule`
