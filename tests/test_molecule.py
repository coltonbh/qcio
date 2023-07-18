import pytest

from qcio import Molecule

from .data import molecules


def test_from_xyz(test_data_dir):
    caffeine = Molecule._from_xyz(test_data_dir / "caffeine.xyz")
    assert caffeine.symbols == molecules.caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine.geometry[i] == pytest.approx(
            molecules.caffeine.geometry[i], rel=1e-9
        )

    assert caffeine.multiplicity == molecules.caffeine.multiplicity
    assert caffeine.charge == molecules.caffeine.charge


def test_to_file_xyz(test_data_dir, tmp_path):
    caffeine = Molecule.open(test_data_dir / "caffeine.xyz")
    caffeine.save(tmp_path / "caffeine_copy.xyz")
    caffeine_copy = Molecule._from_xyz(tmp_path / "caffeine_copy.xyz")
    assert caffeine_copy.symbols == caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine_copy.geometry[i] == pytest.approx(
            caffeine.geometry[i], rel=1e-9
        )
    assert caffeine_copy.multiplicity == caffeine.multiplicity
    assert caffeine_copy.charge == caffeine.charge


def test_to_from_file_json(test_data_dir, tmp_path):
    caffeine = Molecule.open(test_data_dir / "caffeine.xyz")
    caffeine.save(tmp_path / "caffeine_copy.json")
    caffeine_copy = Molecule.open(tmp_path / "caffeine_copy.json")
    assert caffeine_copy.symbols == caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine_copy.geometry[i] == pytest.approx(
            caffeine.geometry[i], rel=1e-9
        )
    assert caffeine_copy.multiplicity == caffeine.multiplicity
    assert caffeine_copy.charge == caffeine.charge


def test_molecule_dict_connectivity(water):
    # Test that connectivity is a list of lists of floats
    dict = water.dict()
    for bond in dict["connectivity"]:
        assert isinstance(bond, list)
        for val in bond:
            assert isinstance(val, float)

    # Ensure the dict still works if connectivity not included
    dict.pop("connectivity")
    water = Molecule(**dict)
    new_dict = water.dict()
    assert "connectivity" not in new_dict
