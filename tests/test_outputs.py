import pickle

import numpy as np
import pytest
from pydantic import ValidationError

from qcio import (
    FileInput,
    Files,
    OptimizationResults,
    ProgramInput,
    ProgramOutput,
    Provenance,
    SinglePointResults,
    Structure,
    Wavefunction,
)


def test_results_gradient_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    gradient = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    results = SinglePointResults(gradient=gradient)
    assert isinstance(results.gradient, np.ndarray)
    assert results.gradient.dtype == np.float64


def test_results_hessian_converted_np_array():
    """Test that SinglePointResult converts gradient to np array"""
    hessian = [float(i) for i in range(9)]
    results = SinglePointResults(hessian=hessian)
    assert isinstance(results.hessian, np.ndarray)
    assert results.hessian.dtype == np.float64


def test_single_point_success_casts_gradient_to_n_by_3(prog_input):
    """Test that SinglePointSuccess casts gradient to n by 3"""
    pi_gradient = prog_input("gradient")
    n_atoms = len(pi_gradient.structure.symbols)
    gradient = [float(i) for i in range(n_atoms * 3)]
    output = ProgramOutput(
        input_data=pi_gradient,
        success=True,
        results={
            "gradient": gradient,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.results.gradient.shape == (n_atoms, 3)
    # Assert that gradient is numpy array of floats
    assert output.results.gradient.dtype == np.float64


def test_single_point_success_casts_hessian_to_3n_by_3n(prog_input):
    """Test that SinglePointSuccess casts hessian to 3n x 3n"""
    pi_hessian = prog_input("hessian")
    n_atoms = len(pi_hessian.structure.symbols)
    hessian = [float(i) for i in range(n_atoms**2 * 3**2)]

    po = ProgramOutput(
        input_data=pi_hessian,
        success=True,
        results={
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert po.results.hessian.shape == (n_atoms * 3, n_atoms * 3)
    # Assert that hessian is numpy array of floats
    assert po.results.hessian.dtype == np.float64


def test_single_point_results_normal_modes_cartesian_shape(prog_input):
    """Test that SinglePointResults normal_modes_cartesian are n_modes x n_atoms x 3"""
    pi_energy = prog_input("energy")
    n_atoms = len(pi_energy.structure.symbols)
    n_atoms * 3
    results = SinglePointResults(
        energy=-1.0,
        freqs_wavenumber=[1.0, 2.0, 3.0],  # Given so there are 3 normal modes
        # fmt: off
        normal_modes_cartesian = np.array([-1.45413605e-07, 7.31568094e-02, 3.49777695e-34, -4.00280118e-01, -5.80603129e-01, 8.72597124e-50, 4.00282426e-01, -5.80601321e-01, -2.61779137e-49, -8.40792347e-07, 4.64736028e-02, -7.85031947e-33, 6.02403552e-01, -3.68838662e-01, -1.08372224e-49, -6.02390207e-01, -3.68828204e-01, 3.25116671e-49, -6.99575075e-02, -7.31659905e-07, 9.73449382e-38, 5.55204565e-01, -4.35072838e-01, 1.17356863e-54, 5.55217962e-01, 4.35084451e-01, -3.52070589e-54])
        # fmt: on
    )
    assert results.normal_modes_cartesian.shape == (3, 3, 3)


def test_return_result(prog_input):
    """Test that return_result returns the requested result"""
    # TODO: Remove this test once you depreciate .return_result
    prog_input_energy = prog_input("energy")
    energy = 1.0
    n_atoms = len(prog_input_energy.structure.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    output = ProgramOutput(
        input_data=prog_input_energy,
        success=True,
        results={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite"},
    )
    assert output.return_result == energy
    assert output.return_result == output.results.energy

    pi_gradient = prog_input("gradient")
    output = ProgramOutput(
        **{**output.model_dump(), **{"input_data": pi_gradient}}
    )  # noqa: E501
    assert np.array_equal(output.return_result, gradient)
    assert np.array_equal(output.return_result, output.results.gradient)

    pi_hessian = prog_input("hessian")
    output = ProgramOutput(**{**output.model_dump(), **{"input_data": pi_hessian}})

    assert np.array_equal(output.return_result, hessian)
    assert np.array_equal(output.return_result, output.results.hessian)


def test_successful_output_serialization(prog_output):
    """Test that successful result serializes and deserializes"""
    serialized = prog_output.model_dump_json()
    deserialized = ProgramOutput.model_validate_json(serialized)
    assert deserialized == prog_output
    assert deserialized.results == prog_output.results
    assert deserialized.input_data == prog_output.input_data
    assert deserialized.provenance.program == "qcio-test-suite"
    assert deserialized.stdout == prog_output.stdout
    assert deserialized.extras == prog_output.extras
    # assert deserialized.return_result == prog_output.return_result
    assert deserialized.results.energy == prog_output.results.energy
    assert np.array_equal(deserialized.results.gradient, prog_output.results.gradient)
    assert np.array_equal(deserialized.results.hessian, prog_output.results.hessian)


def test_wavefunction_to_numpy():
    """Test that wavefunction converts to numpy array"""
    wavefunction = Wavefunction(
        scf_eigenvalues_a=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        scf_eigenvalues_b=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        scf_occupations_a=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        scf_occupations_b=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    )
    assert isinstance(wavefunction.scf_eigenvalues_a, np.ndarray)
    assert isinstance(wavefunction.scf_eigenvalues_b, np.ndarray)
    assert isinstance(wavefunction.scf_occupations_a, np.ndarray)
    assert isinstance(wavefunction.scf_occupations_b, np.ndarray)
    assert wavefunction.scf_eigenvalues_a.dtype == np.float64
    assert wavefunction.scf_eigenvalues_b.dtype == np.float64
    assert wavefunction.scf_occupations_a.dtype == np.float64
    assert wavefunction.scf_occupations_b.dtype == np.float64


def test_correct_generic_instantiates_and_equality_checks_pass(prog_output, tmp_path):
    """
    This test checks the ProgramOutput.model_post_init method to ensure that the
    correct generic types are instantiated and that equality checks pass. It also
    tests the serialization and deserialization of the ProgramOutput class with and
    without types. The point is that end users should be able to ignore generics
    specification for common tasks like opening files and the correct types will be
    set for them.
    """
    output_dict = prog_output.model_dump()
    ## SinglePointResults
    # Do not pass types
    wo_types = ProgramOutput(**output_dict)
    # Pass types
    w_types = ProgramOutput[ProgramInput, SinglePointResults](**output_dict)

    ## OptimizationResults
    output_dict["input_data"]["calctype"] = "optimization"
    output_dict["results"] = OptimizationResults(trajectory=[wo_types])
    # Do not pass types
    wo_types_opt = ProgramOutput(**output_dict)
    # Pass types
    w_types_opt = ProgramOutput[ProgramInput, OptimizationResults](**output_dict)

    # Serialize and Save
    wo_types.save(tmp_path / "out.json")
    w_types_opt.save(tmp_path / "opt.json")

    # Reopen with or without types
    wo_types_opened = ProgramOutput.open(tmp_path / "out.json")
    w_types_opened = ProgramOutput[ProgramInput, SinglePointResults].open(
        tmp_path / "out.json"
    )

    # Reopen with or without types
    wo_types_opened_opt = ProgramOutput.open(tmp_path / "opt.json")
    w_types_opened_opt = ProgramOutput[ProgramInput, OptimizationResults].open(
        tmp_path / "opt.json"
    )

    # Make sure all objects have the same class (with correct types) and values
    assert wo_types == w_types == wo_types_opened == w_types_opened
    assert wo_types_opt == w_types_opt == wo_types_opened_opt == w_types_opened_opt


def test_non_file_success_always_has_result(prog_input):
    pi_energy = prog_input("energy")
    with pytest.raises(ValidationError):
        ProgramOutput[ProgramInput, SinglePointResults](
            success=True,
            input_data=pi_energy,
            stdout="program standard out...",
            results=None,
            provenance={"program": "qcio-test-suite"},
        )


def test_primary_result_must_be_present_on_success(prog_output):
    for calctype in ["energy", "gradient", "hessian"]:
        po_dict = prog_output.model_dump()
        po_dict["input_data"]["calctype"] = calctype
        po_dict["results"][calctype] = None
        with pytest.raises(ValidationError):
            ProgramOutput[ProgramInput, SinglePointResults](**po_dict)


@pytest.mark.parametrize(
    "input_data, results_data, success, expected_input_type, expected_result_type",
    [
        pytest.param(
            "file_input",
            Files(),
            True,
            FileInput,
            Files,
            id="FileInput-Files-Success",
        ),
        pytest.param(
            "file_input",
            Files(),
            False,
            FileInput,
            Files,
            id="FileInput-Files-Failure",
        ),
    ],
    indirect=["input_data"],
)
def test_pickle_serialization_of_program_output_parametrized(
    input_data,
    results_data,
    success,
    expected_input_type,
    expected_result_type,
    request,
):
    """This test checks that all the dynamic types are correctly set when
    deserializing a ProgramOutput object. It also checks that the equality
    checks pass for the deserialized object. It also ensure that the types
    set can be looked up by pickle in qcio.models.outputs.ProgramOutput.s
    """

    provenance = Provenance(program="qcio-test-suite")
    traceback = None
    if success is False:
        traceback = "Fake traceback"

    # Generics specified at instantiation of ProgramOutput
    prog_output = ProgramOutput[type(input_data), type(results_data)](
        input_data=input_data,
        results=results_data,
        success=success,
        provenance=provenance,
        traceback=traceback,
    )
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == prog_output

    # Generics not specified at instantiation of ProgramOutput
    prog_output = ProgramOutput(
        input_data=input_data,
        results=results_data,
        success=success,
        provenance=provenance,
        traceback=traceback,
    )
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == prog_output

    # Generics not specified at instantiation of ProgramOutput
    unspecified_po = ProgramOutput(**prog_output.model_dump())
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == unspecified_po

    # Generics specified and .results is not passed
    prog_output_dict = prog_output.model_dump()
    prog_output_dict.update({"success": False, "traceback": "Traceback: ..."})
    no_results = ProgramOutput(**prog_output_dict)
    serialized = pickle.dumps(no_results)
    deserialized = pickle.loads(serialized)
    assert deserialized == no_results

    # Dynamically specified generics
    dynamic_generics = ProgramOutput[
        type(prog_output.input_data), type(prog_output.results)
    ](**prog_output.model_dump())
    serialized = pickle.dumps(dynamic_generics)
    deserialized = pickle.loads(serialized)
    assert deserialized == dynamic_generics


def test_pickle_serialization_of_program_output():
    prog_output = ProgramOutput[ProgramInput, SinglePointResults](
        input_data=ProgramInput(
            structure=Structure(
                symbols=["O", "H", "H"],
                geometry=np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0, 1.0, 0.0]),
                charge=0,
                multiplicity=1,
                connectivity=[(0, 1, 1.0), (0, 2, 1.0)],
            ),
            calctype="energy",
            model={"method": "hf", "basis": "sto-3g"},
            keywords={
                "maxiter": 100,
                "purify": "no",
                "some-bool": False,
                "displacement": 1e-3,
                "thermo_temp": 298.15,
            },
        ),
        success=True,
        # traceback="Traceback: ...",
        stdout="program standard out...",
        results=SinglePointResults(
            energy=1.0,
            extras={"some_extra_result": 1},
        ),
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )
    # Generics specified at instantiation of ProgramOutput
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == prog_output

    # Generics not specified at instantiation of ProgramOutput
    unspecified_po = ProgramOutput(**prog_output.model_dump())
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == unspecified_po

    # Generics specified and .results is None
    prog_output_dict = prog_output.model_dump()
    prog_output_dict.update(
        {"results": Files(), "success": False, "traceback": "Traceback: ..."}
    )
    # Fails
    no_results = ProgramOutput(**prog_output_dict)
    serialized = pickle.dumps(no_results)
    deserialized = pickle.loads(serialized)
    assert deserialized == no_results

    # Dynamically specified generics
    dynamic_generics = ProgramOutput[
        type(prog_output.input_data), type(prog_output.results)
    ](**prog_output.model_dump())
    serialized = pickle.dumps(dynamic_generics)
    deserialized = pickle.loads(serialized)
    assert deserialized == dynamic_generics


def test_ensure_result_present_on_single_point_results_validator():
    with pytest.raises(ValidationError):
        SinglePointResults()


def test_compatibility_layer_for_files_on_program_output(prog_input):
    """Test that the compatibility layer for files on ProgramOutput works"""
    energy_input = prog_input("energy")
    # Passing Files as a dictionary
    files = {"file1": "file1.txt", "file2": "file2.txt"}

    po = ProgramOutput(
        input_data=energy_input,
        success=True,
        results=SinglePointResults(energy=-1.0),
        provenance={"program": "qcio-test-suite"},
        files=files,
    )
    assert po.results.files == files


def test_compatibility_layer_for_noresults_prog_outputs(test_data_dir):
    """Ensure old ProgramOutput with NoResults can still be loaded."""
    ProgramOutput.model_validate_json((test_data_dir / "po_noresults.json").read_text())
