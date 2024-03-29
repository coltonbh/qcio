from pathlib import Path

import numpy as np
import pytest

from qcio import ProgramInput, SinglePointOutput
from qcio.utils import water as water_mol


@pytest.fixture
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture
def water():
    """Water molecule fixture"""
    return water_mol


@pytest.fixture
def sp_input(water):
    """Create a function that returns a SinglePointInput object with a specified
    calculation type."""

    def _create_sp_input(calctype):
        return ProgramInput(
            molecule=water,
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

    return _create_sp_input


@pytest.fixture
def sp_output(sp_input):
    """Create SinglePointOutput object"""
    sp_inp_energy = sp_input("energy")
    energy = 1.0
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    return SinglePointOutput(
        input_data=sp_inp_energy,
        stdout="program standard out...",
        results={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )
