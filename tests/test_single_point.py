import numpy as np

from qcio import SinglePointOutput, SinglePointResults, Wavefunction


def test_results_gradient_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    gradient = [1, 2, 3, 4, 5, 6]
    results = SinglePointResults(gradient=gradient)
    assert isinstance(results.gradient, np.ndarray)
    assert results.gradient.dtype == np.float64


def test_results_hessian_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    hessian = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    results = SinglePointResults(hessian=hessian)
    assert isinstance(results.hessian, np.ndarray)
    assert results.hessian.dtype == np.float64


def test_single_point_success_casts_gradient_to_n_by_3(sp_input):
    """Test that SinglePointSuccess casts gradient to n by 3"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = [i for i in range(n_atoms * 3)]
    output = SinglePointOutput(
        input_data=sp_inp_energy,
        results={
            "gradient": gradient,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.results.gradient.shape == (n_atoms, 3)
    # Assert that gradient is numpy array of floats
    assert output.results.gradient.dtype == np.float64


def test_single_point_success_casts_hessian_to_3n_by_3n(sp_input):
    """Test that SinglePointSuccess casts hessian to 3n x 3n"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    hessian = [i for i in range(n_atoms**2 * 3**2)]

    output = SinglePointOutput(
        input_data=sp_inp_energy,
        results={
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.results.hessian.shape == (n_atoms * 3, n_atoms * 3)
    # Assert that hessian is numpy array of floats
    assert output.results.hessian.dtype == np.float64


def test_single_point_results_normal_modes_cartesian_shape(sp_input):
    """Test that SinglePointResults normal_modes_cartesian are n_modes x n_atoms x 3"""
    sp_inp_energy = sp_input("energy")
    n_atoms = len(sp_inp_energy.molecule.symbols)
    n_atoms * 3
    results = SinglePointResults(
        normal_modes_cartesian=np.array(
            [
                [
                    -1.45413605e-07,
                    7.31568094e-02,
                    3.49777695e-34,
                    -4.00280118e-01,
                    -5.80603129e-01,
                    8.72597124e-50,
                    4.00282426e-01,
                    -5.80601321e-01,
                    -2.61779137e-49,
                ],
                [
                    -8.40792347e-07,
                    4.64736028e-02,
                    -7.85031947e-33,
                    6.02403552e-01,
                    -3.68838662e-01,
                    -1.08372224e-49,
                    -6.02390207e-01,
                    -3.68828204e-01,
                    3.25116671e-49,
                ],
                [
                    -6.99575075e-02,
                    -7.31659905e-07,
                    9.73449382e-38,
                    5.55204565e-01,
                    -4.35072838e-01,
                    1.17356863e-54,
                    5.55217962e-01,
                    4.35084451e-01,
                    -3.52070589e-54,
                ],
            ]
        )
    )
    assert results.normal_modes_cartesian.shape == (3, 3, 3)


def test_return_result(sp_input):
    """Test that return_result returns the requested result"""
    sp_inp_energy = sp_input("energy")
    energy = 1.0
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    output = SinglePointOutput(
        input_data=sp_inp_energy,
        results={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.return_result == energy
    assert output.return_result == output.results.energy

    sp_inp_grad = sp_input("gradient")
    output = SinglePointOutput(**{**output.dict(), **{"input_data": sp_inp_grad}})

    assert np.array_equal(output.return_result, gradient)
    assert np.array_equal(output.return_result, output.results.gradient)

    sp_inp_hessian = sp_input("hessian")
    output = SinglePointOutput(**{**output.dict(), **{"input_data": sp_inp_hessian}})

    assert np.array_equal(output.return_result, hessian)
    assert np.array_equal(output.return_result, output.results.hessian)


def test_successful_output_serialization(sp_output):
    """Test that successful result serializes and deserializes"""
    serialized = sp_output.json()
    # model_validate_json in pydantic v2
    deserialized = SinglePointOutput.parse_raw(serialized)
    assert deserialized == sp_output
    assert deserialized.results == sp_output.results
    assert deserialized.input_data == sp_output.input_data
    assert deserialized.provenance.program == "qcio-test-suite"
    assert deserialized.stdout == sp_output.stdout
    assert deserialized.extras == sp_output.extras
    assert deserialized.return_result == sp_output.return_result
    assert deserialized.return_result == sp_output.results.energy
    assert np.array_equal(deserialized.results.gradient, sp_output.results.gradient)
    assert np.array_equal(deserialized.results.hessian, sp_output.results.hessian)


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
