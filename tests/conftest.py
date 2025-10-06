from pathlib import Path

import numpy as np
import pytest

from qcio import (
    CalcSpec,
    CompositeCalcSpec,
    Files,
    FileSpec,
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
    return FileSpec(
        files={"binary": b"binary data", "text": "text data"},
        cmdline_args=["-i", "input.dat", "-o", "output.dat"],
    )


@pytest.fixture
def input_data(request, file_input, calc_input, ccalc_input):
    """Input data fixture"""
    if request.param == "file_input":
        return file_input
    elif request.param == "calc_input":
        return calc_input("energy")
    elif request.param == "ccalc_input":  # CompositeCalcSpec
        return ccalc_input
    else:
        raise ValueError(f"Unknown input data type: {request.param}")


@pytest.fixture
def calc_input(water):
    """Function that returns CalcSpec of calctype."""

    def _create_calc_input(calctype):
        return CalcSpec(
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

    return _create_calc_input


@pytest.fixture
def ccalc_input(water):
    """Function that returns CompositeCalcSpec of calctype."""

    def _create_calc_input(calctype):
        return CompositeCalcSpec(
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

    return _create_calc_input


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
def results(calc_input, sp_data):
    """Successful Results object"""
    pi_energy = calc_input("energy")
    sp_data = sp_data(pi_energy.structure)

    return Results[CalcSpec, SinglePointData](
        input_data=pi_energy,
        success=True,
        logs="program standard out...",
        data=sp_data,
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture
def results_failure(calc_input, sp_data):
    """Failed Results object"""
    ci_energy = calc_input("energy")

    return Results[CalcSpec, Files](
        input_data=ci_energy,
        success=False,
        traceback="Traceback...",
        data=Files(),
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture
def opt_data(results):
    return OptimizationData(trajectory=[results])
