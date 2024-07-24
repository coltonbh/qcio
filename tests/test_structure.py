import numpy as np
import pytest

from qcio import Structure

from .data import structures


def test_from_xyz(test_data_dir):
    xyz_str = (test_data_dir / "caffeine.xyz").read_text()
    caffeine = Structure.from_xyz(xyz_str)
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
    caffeine_copy = Structure.open(tmp_path / "caffeine_copy.xyz")
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
    struct = Structure.from_smiles("OCC", program="rdkit", force_field="UFF")
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
    assert struct.identifiers.smiles == "OCC"
    assert struct.identifiers.canonical_smiles == "CCO"

    # Check Charge
    struct = Structure.from_smiles("[O-]CC")
    assert struct.charge == -1

    # Check manual multiplicity
    struct = Structure.from_smiles("[O-]CC", multiplicity=3)
    assert struct.charge == -1
    assert struct.multiplicity == 3


def test_smiles_to_structure_openbabel():
    struct = Structure.from_smiles("OCC", program="openbabel")
    assert struct.symbols == ["O", "C", "C", "H", "H", "H", "H", "H", "H"]
    assert struct.charge == 0
    assert struct.multiplicity == 1
    assert struct.identifiers.smiles == "OCC"
    assert struct.identifiers.canonical_smiles == "CCO"

    # Check Charge
    struct = Structure.from_smiles("[O-]CC")
    assert struct.charge == -1

    # Check manual multiplicity
    struct = Structure.from_smiles("[O-]CC", multiplicity=3)
    assert struct.charge == -1
    assert struct.multiplicity == 3


def test_ids_backwards_compatibility():
    struct = Structure(symbols=["H"], geometry=[[0, 0, 0]], ids={"name": "fake"})
    assert struct.identifiers.name == "fake"
    # Test that ids is an alias for identifiers
    assert struct.ids == struct.identifiers


@pytest.mark.parametrize(
    "xyzstring, charge, multiplicity, expected_charge, expected_multiplicity, raises",
    [
        (
            """2
            
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            1,
            None,
            1,
            1,
            False,
        ),
        (
            """2
            
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            None,
            2,
            0,
            2,
            False,
        ),
        (
            """2
            
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            3,
            4,
            3,
            4,
            False,
        ),
        (
            """2
            qcio_charge=-3
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            None,
            2,
            -3,
            2,
            False,
        ),
        (
            """2
            qcio_charge=-3
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            1,
            None,
            None,
            None,
            True,
        ),
        (
            """2
            qcio_multiplicity=4
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            1,
            None,
            1,
            4,
            False,
        ),
        (
            """2
            qcio_multiplicity=4
            H 0.0 0.0 0.0
            H 0.0 0.0 1.0
            """,
            None,
            1,
            None,
            None,
            True,
        ),
    ],
)
def test_passing_charge_and_multiplicity_to_open(
    tmp_path,
    xyzstring,
    charge,
    multiplicity,
    expected_charge,
    expected_multiplicity,
    raises,
):
    filepath = tmp_path / "test.xyz"
    filepath.write_text(xyzstring)

    if raises:
        with pytest.raises(ValueError):
            struct = Structure.open(filepath, charge=charge, multiplicity=multiplicity)
    else:
        struct = Structure.open(filepath, charge=charge, multiplicity=multiplicity)
        assert struct.charge == expected_charge
        assert struct.multiplicity == expected_multiplicity


def test_no_charge_multiplicity_to_non_xyz_files():
    with pytest.raises(ValueError):
        Structure.open("file.json", charge=1, multiplicity=2)


def test_to_smiles_rdkit(water):
    smiles = water.to_smiles()
    assert smiles == "O"
    smiles = water.to_smiles(program="rdkit", hydrogens=True)
    assert smiles == "[H]O[H]"


def test_to_smiles_openbabel(water):
    smiles = water.to_smiles()
    assert smiles == "O"
    smiles = water.to_smiles(program="openbabel", hydrogens=True)
    assert smiles == "[H]O[H]"


def test_add_smiles(water):
    water.add_smiles(program="rdkit")
    assert water.identifiers.smiles == "O"
    assert water.identifiers.canonical_smiles == "O"
    assert water.identifiers.canonical_smiles_program == "rdkit"
    water.add_smiles(program="rdkit", hydrogens=True)
    assert water.identifiers.canonical_explicit_hydrogen_smiles == "[H]O[H]"

    water.add_smiles(program="openbabel")
    assert water.identifiers.smiles == "O"
    assert water.identifiers.canonical_smiles == "O"
    assert water.identifiers.canonical_smiles_program == "openbabel"
    water.add_smiles(program="openbabel", hydrogens=True)
    assert water.identifiers.canonical_explicit_hydrogen_smiles == "[H]O[H]"
