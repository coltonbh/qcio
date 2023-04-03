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
    caffeine = Molecule.from_file(test_data_dir / "caffeine.xyz")
    caffeine.to_file(tmp_path / "caffeine_copy.xyz")
    caffeine_copy = Molecule._from_xyz(tmp_path / "caffeine_copy.xyz")
    assert caffeine_copy.symbols == caffeine.symbols
    for i in range(len(caffeine.geometry)):
        assert caffeine_copy.geometry[i] == pytest.approx(
            caffeine.geometry[i], rel=1e-9
        )
    assert caffeine_copy.multiplicity == caffeine.multiplicity
    assert caffeine_copy.charge == caffeine.charge
