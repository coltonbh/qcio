from pathlib import Path

import numpy as np
import pytest

from qcio import (
    DualProgramInput,
    FileInput,
    Files,
    OptimizationData,
    ProgramArgs,
    ProgramInput,
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
def input_data(request, file_input, prog_input_factory, dprog_input_factory):
    """Input data fixture"""
    if request.param == "file_input":
        return file_input
    elif request.param == "calc_input":
        return prog_input_factory("energy")
    elif request.param == "ccalc_input":  # DualProgramInput
        return dprog_input_factory
    else:
        raise ValueError(f"Unknown input data type: {request.param}")


@pytest.fixture
def prog_input_factory(water):
    """Function that returns ProgramInput of calctype."""

    def _create_prog_inp(calctype):
        return ProgramInput(
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

    return _create_prog_inp


@pytest.fixture
def dprog_input_factory(water):
    """Function that returns DualProgramInput of calctype."""

    def _create_prog_inp(calctype):
        return DualProgramInput(
            structure=water,
            calctype=calctype,
            keywords={
                "maxiter": 100,
                "purify": "no",
                "some-bool": False,
            },
            subprogram="fake subprogram",
            subprogram_args=ProgramArgs(model={"method": "hf", "basis": "sto-3g"}),
        )

    return _create_prog_inp


@pytest.fixture
def sp_data():
    """SinglePointData object"""

    def _create_sp_data(structure):
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

    return _create_sp_data


@pytest.fixture
def results(prog_input_factory, sp_data):
    """Successful Results object"""
    pi_energy = prog_input_factory("energy")
    sp_data = sp_data(pi_energy.structure)

    return Results[ProgramInput, SinglePointData](
        input_data=pi_energy,
        success=True,
        logs="program standard out...",
        data=sp_data,
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture
def results_failure(prog_input_factory, sp_data):
    """Failed Results object"""
    pi_energy = prog_input_factory("energy")

    return Results[ProgramInput, Files](
        input_data=pi_energy,
        success=False,
        traceback="Traceback...",
        data=Files(),
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture
def opt_data(results):
    return OptimizationData(trajectory=[results])
