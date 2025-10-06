"""Test tools enabling compatibility with QCElemental"""

import numpy as np
from qcelemental.models import AtomicInput, AtomicResult

# from qcio import ProgramFailure
from qcio.qcel import from_qcel_output_results, to_qcel_input


def test_input_to_qcel(calc_input):
    """Test that input converts to qcel input"""
    ci_energy = calc_input("energy")
    qcel_input_dict = to_qcel_input(ci_energy)
    qcel_atomic_input = AtomicInput(**qcel_input_dict)

    assert qcel_atomic_input.molecule.symbols.tolist() == ci_energy.structure.symbols
    assert np.array_equal(
        qcel_atomic_input.molecule.geometry, ci_energy.structure.geometry
    )
    assert qcel_atomic_input.molecule.molecular_charge == ci_energy.structure.charge
    assert qcel_atomic_input.model.method == ci_energy.model.method
    assert qcel_atomic_input.model.basis == ci_energy.model.basis
    assert qcel_atomic_input.driver == "energy"
    assert qcel_atomic_input.keywords == ci_energy.keywords
    assert qcel_atomic_input.extras == ci_energy.extras


def test_input_to_output_from_qcel_output_with_wfn(calc_input):
    """Test that input converts to qcel input"""
    ci_energy = calc_input("energy")

    # Check that the input converts to a qcel input
    qcel_atomic_input = AtomicInput(**to_qcel_input(ci_energy))

    qcel_atomic_output = AtomicResult(
        **{
            **qcel_atomic_input.dict(),
            **{
                "protocols": {"wavefunction": "all"},
                "properties": {
                    "nuclear_repulsion_energy": 1.0,
                    "return_energy": 1.0,
                    "calcinfo_natom": 3,
                },
                "return_result": 1.0,
                "success": True,
                "wavefunction": {
                    "scf_eigenvalues_a": [1, 2, 3, 4, 5, 6],
                    "restricted": True,
                    "basis": {
                        "name": "6-31g",
                        "center_data": {},
                        "atom_map": [],
                    },
                },
            },
        },
    )
    results = from_qcel_output_results(qcel_atomic_output.dict())

    assert results.energy == qcel_atomic_output.return_result
    assert (
        results.nuclear_repulsion_energy
        == qcel_atomic_output.properties.nuclear_repulsion_energy
    )
    assert results.calcinfo_natoms == qcel_atomic_output.properties.calcinfo_natom


def test_input_to_output_from_qcel_output_no_wfn(calc_input):
    """Test that input converts to qcel input"""
    calc_input_energy = calc_input("energy")
    qcel_atomic_input = AtomicInput(**to_qcel_input(calc_input_energy))

    qcel_atomic_output = AtomicResult(
        **{
            **qcel_atomic_input.dict(),
            **{
                "properties": {
                    "nuclear_repulsion_energy": 1.0,
                    "return_energy": 1.0,
                    "calcinfo_natom": 3,
                },
                "return_result": 1.0,
                "success": True,
            },
        },
    )
    results = from_qcel_output_results(qcel_atomic_output.dict())

    assert results.energy == qcel_atomic_output.return_result
    assert (
        results.nuclear_repulsion_energy
        == qcel_atomic_output.properties.nuclear_repulsion_energy
    )
    assert results.calcinfo_natoms == qcel_atomic_output.properties.calcinfo_natom
