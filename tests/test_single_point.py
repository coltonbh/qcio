import numpy as np

from qcio import (
    Provenance,
    SinglePointComputedProperties,
    SinglePointSuccessfulOutput,
    Wavefunction,
)


def test_computed_gradient_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    gradient = [1, 2, 3, 4, 5, 6]
    result = SinglePointComputedProperties(gradient=gradient)
    assert isinstance(result.gradient, np.ndarray)
    assert result.gradient.dtype == np.float64


def test_computed_hessian_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    hessian = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    result = SinglePointComputedProperties(hessian=hessian)
    assert isinstance(result.hessian, np.ndarray)
    assert result.hessian.dtype == np.float64


def test_single_point_success_casts_gradient_to_n_by_3(sp_input):
    """Test that SinglePointSuccess casts gradient to n by 3"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = [i for i in range(n_atoms * 3)]
    success = SinglePointSuccessfulOutput(
        input_data=sp_inp_energy,
        computed={
            "gradient": gradient,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert success.computed.gradient.shape == (n_atoms, 3)
    # Assert that gradient is numpy array of floats
    assert success.computed.gradient.dtype == np.float64


def test_single_point_success_casts_hessian_to_3n_by_3n(sp_input):
    """Test that SinglePointSuccess casts hessian to 3n x 3n"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    hessian = [i for i in range(n_atoms**2 * 3**2)]

    output = SinglePointSuccessfulOutput(
        input_data=sp_inp_energy,
        computed={
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.computed.hessian.shape == (n_atoms * 3, n_atoms * 3)
    # Assert that hessian is numpy array of floats
    assert output.computed.hessian.dtype == np.float64


def test_return_result(sp_input):
    """Test that return_result returns the requested result"""
    sp_inp_energy = sp_input("energy")
    energy = 1.0
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    output = SinglePointSuccessfulOutput(
        input_data=sp_inp_energy,
        computed={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.return_result == energy
    assert output.return_result == output.computed.energy

    sp_inp_grad = sp_input("gradient")
    output = SinglePointSuccessfulOutput(
        **{**output.dict(), **{"input_data": sp_inp_grad}}
    )

    assert np.array_equal(output.return_result, gradient)
    assert np.array_equal(output.return_result, output.computed.gradient)

    sp_inp_hessian = sp_input("hessian")
    output = SinglePointSuccessfulOutput(
        **{**output.dict(), **{"input_data": sp_inp_hessian}}
    )

    assert np.array_equal(output.return_result, hessian)
    assert np.array_equal(output.return_result, output.computed.hessian)


def test_successful_output_serialization(sp_successful_output):
    """Test that successful result serializes and deserializes"""
    serialized = sp_successful_output.json()
    # model_validate_json in pydantic v2
    deserialized = SinglePointSuccessfulOutput.parse_raw(serialized)
    assert deserialized == sp_successful_output
    assert deserialized.computed == sp_successful_output.computed
    assert deserialized.input_data == sp_successful_output.input_data
    assert deserialized.provenance == Provenance(program="qcio-test-suite")
    assert deserialized.stdout == sp_successful_output.stdout
    assert deserialized.extras == sp_successful_output.extras
    assert deserialized.return_result == sp_successful_output.return_result
    assert deserialized.return_result == sp_successful_output.computed.energy
    assert np.array_equal(
        deserialized.computed.gradient, sp_successful_output.computed.gradient
    )
    assert np.array_equal(
        deserialized.computed.hessian, sp_successful_output.computed.hessian
    )


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
