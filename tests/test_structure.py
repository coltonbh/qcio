import numpy as np
import pytest

from qcio import Structure

from .data import structures


def test_from_xyz(test_data_dir):
    caffeine = Structure._from_xyz(test_data_dir / "caffeine.xyz")
    assert caffeine.symbols == structures.caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine.geometry[i] == pytest.approx(
            structures.caffeine.geometry[i], rel=1e-9
        )

    assert caffeine.multiplicity == structures.caffeine.multiplicity
    assert caffeine.charge == structures.caffeine.charge


def test_to_file_xyz(test_data_dir, tmp_path):
    caffeine = Structure.open(test_data_dir / "caffeine.xyz")
    caffeine.save(tmp_path / "caffeine_copy.xyz")
    caffeine_copy = Structure._from_xyz(tmp_path / "caffeine_copy.xyz")
    assert caffeine_copy.symbols == caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine_copy.geometry[i] == pytest.approx(
            caffeine.geometry[i], rel=1e-9
        )
    assert caffeine_copy.multiplicity == caffeine.multiplicity
    assert caffeine_copy.charge == caffeine.charge

    # single \n at end of file
    text = (tmp_path / "caffeine_copy.xyz").read_text()
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_to_from_file_json(test_data_dir, tmp_path):
    caffeine = Structure.open(test_data_dir / "caffeine.xyz")
    caffeine.save(tmp_path / "caffeine_copy.json")
    caffeine_copy = Structure.open(tmp_path / "caffeine_copy.json")
    assert caffeine_copy.symbols == caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine_copy.geometry[i] == pytest.approx(
            caffeine.geometry[i], rel=1e-9
        )
    assert caffeine_copy.multiplicity == caffeine.multiplicity
    assert caffeine_copy.charge == caffeine.charge


def test_structure_model_dump_connectivity(water):
    # Test that connectivity is a list of lists of floats
    # Must cast all to the same type as toml cannot handle mixed types
    dict = water.model_dump()
    for bond in dict["connectivity"]:
        assert isinstance(bond, list)
        for val in bond:
            assert isinstance(val, float)


def test_structure_capitalize():
    structure = Structure(symbols=["NA"], geometry=[[0, 0, 0]])
    assert structure.symbols == ["Na"]
    structure = Structure(symbols=["h"], geometry=[[0, 0, 0]])
    assert structure.symbols == ["H"]


def test_atomic_symbols():
    structure = Structure(symbols=["Na", "Cl"], geometry=[[0, 0, 0], [1, 1, 1]])
    assert structure.atomic_numbers == [11, 17]


def test_smiles_to_structure_rdkit():
    struct = Structure.from_smiles("OCC")
    assert struct.symbols == ["O", "C", "C", "H", "H", "H", "H", "H", "H"]
    assert np.allclose(
        struct.geometry,
        [
            [2.6979441, -1.06763753, -0.62153908],
            [0.88868167, 0.83954245, -0.29985753],
            [-1.72671851, -0.31066038, 0.05825528],
            [3.02616491, -1.78814426, 1.07956874],
            [0.87558876, 2.05322739, -2.01164947],
            [1.37464628, 2.04828289, 1.35295762],
            [-1.76163293, -1.49808375, 1.78844384],
            [-3.15050459, 1.21801804, 0.2556908],
            [-2.22416969, -1.49454485, -1.60187022],
        ],
        atol=1e-4,
    )
    assert struct.charge == 0
    assert struct.multiplicity == 1
    assert struct.ids.smiles == "OCC"
    assert struct.ids.canonical_smiles == "CCO"

    # Check Charge
    struct = Structure.from_smiles("[O-]CC")
    assert struct.charge == -1

    # Check manual multiplicity
    struct = Structure.from_smiles("[O-]CC", multiplicity=3)
    assert struct.charge == -1
    assert struct.multiplicity == 3
