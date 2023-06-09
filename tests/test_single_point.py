import numpy as np
from qcelemental.models import AtomicInput, AtomicResult, FailedOperation

from qcio import (
    Provenance,
    SinglePointComputedProps,
    SinglePointFailure,
    SinglePointResult,
    Wavefunction,
)


def test_computed_gradient_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    gradient = [1, 2, 3, 4, 5, 6]
    computed = SinglePointComputedProps(gradient=gradient)
    assert isinstance(computed.gradient, np.ndarray)
    assert computed.gradient.dtype == np.float64


def test_computed_hessian_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    hessian = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    computed = SinglePointComputedProps(hessian=hessian)
    assert isinstance(computed.hessian, np.ndarray)
    assert computed.hessian.dtype == np.float64


def test_single_point_success_casts_gradient_to_n_by_3(sp_input):
    """Test that SinglePointSuccess casts gradient to n by 3"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = [i for i in range(n_atoms * 3)]
    result = SinglePointResult(
        input_data=sp_inp_energy,
        computed={
            "gradient": gradient,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert result.computed.gradient.shape == (n_atoms, 3)
    # Assert that gradient is numpy array of floats
    assert result.computed.gradient.dtype == np.float64


def test_single_point_success_casts_hessian_to_3n_by_3n(sp_input):
    """Test that SinglePointSuccess casts hessian to 3n x 3n"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    hessian = [i for i in range(n_atoms**2 * 3**2)]

    result = SinglePointResult(
        input_data=sp_inp_energy,
        computed={
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert result.computed.hessian.shape == (n_atoms * 3, n_atoms * 3)
    # Assert that hessian is numpy array of floats
    assert result.computed.hessian.dtype == np.float64


def test_return_result(sp_input):
    """Test that return_result returns the requested result"""
    sp_inp_energy = sp_input("energy")
    energy = 1.0
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    result = SinglePointResult(
        input_data=sp_inp_energy,
        computed={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert result.return_result == energy
    assert result.return_result == result.computed.energy

    sp_inp_grad = sp_input("gradient")
    result = SinglePointResult(**{**result.dict(), **{"input_data": sp_inp_grad}})

    assert np.array_equal(result.return_result, gradient)
    assert np.array_equal(result.return_result, result.computed.gradient)

    sp_inp_hessian = sp_input("hessian")
    result = SinglePointResult(**{**result.dict(), **{"input_data": sp_inp_hessian}})

    assert np.array_equal(result.return_result, hessian)
    assert np.array_equal(result.return_result, result.computed.hessian)


def test_successful_output_serialization(sp_result):
    """Test that successful result serializes and deserializes"""
    serialized = sp_result.json()
    # model_validate_json in pydantic v2
    deserialized = SinglePointResult.parse_raw(serialized)
    assert deserialized == sp_result
    assert deserialized.computed == sp_result.computed
    assert deserialized.input_data == sp_result.input_data
    assert deserialized.provenance.program == "qcio-test-suite"
    assert deserialized.stdout == sp_result.stdout
    assert deserialized.extras == sp_result.extras
    assert deserialized.return_result == sp_result.return_result
    assert deserialized.return_result == sp_result.computed.energy
    assert np.array_equal(deserialized.computed.gradient, sp_result.computed.gradient)
    assert np.array_equal(deserialized.computed.hessian, sp_result.computed.hessian)


def test_to_failure(sp_input):
    """Test that to_failure returns a failure result"""
    sp_inp_energy = sp_input("energy")
    provenance = Provenance(program="qcio-test-suite")
    failure = sp_inp_energy.to_failure(provenance, Exception("Test failure"))
    assert failure.input_data == sp_inp_energy
    assert failure.provenance == provenance
    assert failure.extras == sp_inp_energy.extras


def test_wavefunction_to_numpy():
    """Test that wavefunction converts to numpy array"""
    wavefunction = Wavefunction(
        scf_eigenvalues_a=[1, 2, 3, 4, 5, 6],
        scf_eigenvalues_b=[1, 2, 3, 4, 5, 6],
        scf_occupations_a=[1, 2, 3, 4, 5, 6],
        scf_occupations_b=[1, 2, 3, 4, 5, 6],
    )
    assert isinstance(wavefunction.scf_eigenvalues_a, np.ndarray)
    assert isinstance(wavefunction.scf_eigenvalues_b, np.ndarray)
    assert isinstance(wavefunction.scf_occupations_a, np.ndarray)
    assert isinstance(wavefunction.scf_occupations_b, np.ndarray)
    assert wavefunction.scf_eigenvalues_a.dtype == np.float64
    assert wavefunction.scf_eigenvalues_b.dtype == np.float64
    assert wavefunction.scf_occupations_a.dtype == np.float64
    assert wavefunction.scf_occupations_b.dtype == np.float64


def test_input_to_qcel(sp_input):
    """Test that input converts to qcel input"""
    sp_inp_energy = sp_input("energy")
    qcel_input_dict = sp_inp_energy.to_qcel()
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
    qcel_atomic_input = AtomicInput(**sp_inp_energy.to_qcel())

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
    result = sp_inp_energy.to_output_from_qcel(qcel_atomic_output.dict())

    assert result.input_data == sp_inp_energy
    assert result.computed.energy == qcel_atomic_output.return_result
    assert (
        result.computed.nuclear_repulsion_energy
        == qcel_atomic_output.properties.nuclear_repulsion_energy
    )
    assert (
        result.computed.calcinfo_natoms == qcel_atomic_output.properties.calcinfo_natom
    )


def test_input_to_output_from_qcel_output_no_wfn(sp_input):
    """Test that input converts to qcel input"""
    sp_inp_energy = sp_input("energy")
    qcel_atomic_input = AtomicInput(**sp_inp_energy.to_qcel())

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
    result = sp_inp_energy.to_output_from_qcel(qcel_atomic_output.dict())

    assert result.input_data == sp_inp_energy
    assert result.computed.energy == qcel_atomic_output.return_result
    assert (
        result.computed.nuclear_repulsion_energy
        == qcel_atomic_output.properties.nuclear_repulsion_energy
    )
    assert (
        result.computed.calcinfo_natoms == qcel_atomic_output.properties.calcinfo_natom
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

    failure = sp_inp_energy.to_output_from_qcel(failed_operation.dict())
    assert isinstance(failure, SinglePointFailure)
    assert failure.input_data == sp_inp_energy
    assert failure.traceback == failed_operation.error.error_message
    assert failure.extras == failed_operation.extras
