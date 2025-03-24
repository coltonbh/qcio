from collections import defaultdict

import numpy as np
from rdkit import Chem

from qcio import Structure
from qcio.utils import _rdkit_determine_connectivity, _rdkit_mol_from_structure


def get_ranks(struct: Structure) -> list:
    # Convert to rdkit Mol
    mol = _rdkit_mol_from_structure(struct)
    _rdkit_determine_connectivity(mol, struct.charge)

    # Get canonical ranks
    ranks = list(Chem.CanonicalRankAtoms(mol, breakTies=False))

    return ranks


def reorder_atoms_custom(struct: Structure) -> Structure:
    # Get canonical ranks
    ranks = get_ranks(struct)

    # Group indices by rank
    groups = defaultdict(list)
    for idx, rank in enumerate(ranks):
        groups[rank].append(idx)

    # Define tie-breaker function that captures `struct`
    def tie_breaker_key(i):
        # Get the coordinates for atom i.
        coords = struct.geometry[i]
        # Compute the Euclidean norm and round it.
        norm = round(np.linalg.norm(coords), 5)
        # Round each coordinate.
        x, y, z = (round(coord, 5) for coord in coords)
        # Return a tuple that first sorts by norm, then by x, y, and z.
        return (norm, x, y, z)

    # Build final ordering: sort groups by rank, then tie-break within each group.
    final_order = []
    for rank in sorted(groups.keys()):
        group = groups[rank]
        # Tie-breaker: sort by rounded coordinates (as a tuple) to a fixed precision.
        # group.sort(key=lambda i: tuple(round(coord, 1) for coord in struct.geometry[i]))
        # group.sort(key=lambda i: struct.geometry[i][2])
        group.sort(key=tie_breaker_key)
        final_order.extend(group)

    new_symbols = [struct.symbols[i] for i in final_order]
    new_geometry = [struct.geometry[i] for i in final_order]

    nstruct_dict = struct.model_dump()
    nstruct_dict["symbols"] = new_symbols
    nstruct_dict["geometry"] = new_geometry
    return Structure.model_validate(nstruct_dict)


if __name__ == "__main__":
    import sys
    struct = Structure.open(sys.argv[1])
    ranks = get_ranks(struct)
    # Group indices by rank
    groups = defaultdict(list)
    for idx, rank in enumerate(ranks):
        groups[rank].append(idx)
    print(ranks)
    print(groups)
