from pathlib import Path

import numpy as np
import pytest

from qcio import (
    CalcInput,
    CompositeCalcInput,
    FileInput,
    Files,
    OptimizationData,
    Results,
    SinglePointData,
)
from qcio.utils import water as water_struct


@pytest.fixture
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture
def water():
    """Water Structure fixture"""
    return water_struct


@pytest.fixture
def file_input():
    return FileInput(
        files={"binary": b"binary data", "text": "text data"},
        cmdline_args=["-i", "input.dat", "-o", "output.dat"],
    )


@pytest.fixture
def input_data(request, file_input, prog_input, dprog_input):
    """Input data fixture"""
    if request.param == "file_input":
        return file_input
    elif request.param == "prog_input":
        return prog_input("energy")
    elif request.param == "dprog_input":  # CompositeCalcInput
        return dprog_input
    else:
        raise ValueError(f"Unknown input data type: {request.param}")


@pytest.fixture
def prog_input(water):
    """Function that returns CalcInput of calctype."""

    def _create_prog_input(calctype):
        return CalcInput(
            structure=water,
            calctype=calctype,
            model={"method": "hf", "basis": "sto-3g"},
            keywords={
                "maxiter": 100,
                "purify": "no",
                "some-bool": False,
                "displacement": 1e-3,
                "thermo_temp": 298.15,
            },
        )

    return _create_prog_input


@pytest.fixture
def dprog_input(water):
    """Function that returns CompositeCalcInput of calctype."""

    def _create_prog_input(calctype):
        return CompositeCalcInput(
            structure=water,
            calctype=calctype,
            keywords={
                "maxiter": 100,
                "purify": "no",
                "some-bool": False,
            },
            subprogram="fake subprogram",
            subprogram_args={"model": {"method": "hf", "basis": "sto-3g"}},
        )

    return _create_prog_input


@pytest.fixture
def sp_results():
    """SinglePointResults object"""

    def _create_sp_results(structure):
        n_atoms = len(structure.symbols)
        gradient = np.arange(n_atoms * 3, dtype=np.float64).reshape(n_atoms, 3)
        hessian = np.arange(n_atoms**2 * 3**2, dtype=np.float64).reshape(
            n_atoms * 3, n_atoms * 3
        )
        return SinglePointData(
            energy=1.0,
            gradient=gradient,
            hessian=hessian,
            extras={"some_extra_result": 1},
        )

    return _create_sp_results


@pytest.fixture
def prog_output(prog_input, sp_results):
    """Successful ProgramOutput object"""
    pi_energy = prog_input("energy")
    sp_results = sp_results(pi_energy.structure)

    return Results[CalcInput, SinglePointData](
        input_data=pi_energy,
        success=True,
        stdout="program standard out...",
        data=sp_results,
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture
def prog_output_failure(prog_input, sp_results):
    """Failed ProgramOutput object"""
    pi_energy = prog_input("energy")

    return Results[CalcInput, Files](
        input_data=pi_energy,
        success=False,
        traceback="Traceback...",
        data=Files(),
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture
def opt_results(prog_output):
    return OptimizationData(trajectory=[prog_output])
