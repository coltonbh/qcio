"""Test tools enabling compatibility with QCElemental"""

import numpy as np
from qcelemental.models import AtomicInput, AtomicResult, FailedOperation

from qcio import ProgramFailure
from qcio.qcel import from_qcel_output, to_qcel_input


def test_input_to_qcel(sp_input):
    """Test that input converts to qcel input"""
    sp_inp_energy = sp_input("energy")
    qcel_input_dict = to_qcel_input(sp_inp_energy)
    qcel_atomic_input = AtomicInput(**qcel_input_dict)

    assert qcel_atomic_input.molecule.symbols.tolist() == sp_inp_energy.molecule.symbols
    assert np.array_equal(
        qcel_atomic_input.molecule.geometry, sp_inp_energy.molecule.geometry
    )
    assert qcel_atomic_input.molecule.molecular_charge == sp_inp_energy.molecule.charge
    assert qcel_atomic_input.model.method == sp_inp_energy.model.method
    assert qcel_atomic_input.model.basis == sp_inp_energy.model.basis
    assert qcel_atomic_input.driver == "energy"
    assert qcel_atomic_input.keywords == sp_inp_energy.keywords
    assert qcel_atomic_input.extras == sp_inp_energy.extras


def test_input_to_output_from_qcel_output_with_wfn(sp_input):
    """Test that input converts to qcel input"""
    sp_inp_energy = sp_input("energy")

    # Check that the input converts to a qcel input
    qcel_atomic_input = AtomicInput(**to_qcel_input(sp_inp_energy))

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
    output = from_qcel_output(sp_inp_energy, qcel_atomic_output.dict())

    assert output.input_data == sp_inp_energy
    assert output.results.energy == qcel_atomic_output.return_result
    assert (
        output.results.nuclear_repulsion_energy
        == qcel_atomic_output.properties.nuclear_repulsion_energy
    )
    assert (
        output.results.calcinfo_natoms == qcel_atomic_output.properties.calcinfo_natom
    )


def test_input_to_output_from_qcel_output_no_wfn(sp_input):
    """Test that input converts to qcel input"""
    sp_inp_energy = sp_input("energy")
    qcel_atomic_input = AtomicInput(**to_qcel_input(sp_inp_energy))

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
    output = from_qcel_output(sp_inp_energy, qcel_atomic_output.dict())

    assert output.input_data == sp_inp_energy
    assert output.results.energy == qcel_atomic_output.return_result
    assert (
        output.results.nuclear_repulsion_energy
        == qcel_atomic_output.properties.nuclear_repulsion_energy
    )
    assert (
        output.results.calcinfo_natoms == qcel_atomic_output.properties.calcinfo_natom
    )


def test_input_to_output_from_qcel_failed_operation(sp_input):
    """Test that .to_output_from_qcel() returns SinglePointFailedOperation when qcel
    output is a failure.
    """
    failed_operation = FailedOperation(
        error={
            "error_type": "test_error",
            "error_message": "test_error_message",
        },
        extras={"test_error_extra": "test_error_extra_value"},
        input_data={
            "provenance": {
                "creator": "some-program",
                "version": "0.0.0",
            }
        },
    )

    sp_inp_energy = sp_input("energy")

    output = from_qcel_output(sp_inp_energy, failed_operation.dict())
    assert isinstance(output, ProgramFailure)
    assert output.input_data == sp_inp_energy
    assert output.traceback == failed_operation.error.error_message
    assert output.extras == failed_operation.extras
