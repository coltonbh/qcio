import numpy as np
import pytest

from qcio import Structure

from .data import structures as qcio_structures


def test_from_xyz(test_data_dir):
    xyz_str = (test_data_dir / "caffeine.xyz").read_text()
    caffeine = Structure.from_xyz(xyz_str)
    assert caffeine.symbols == qcio_structures.caffeine.symbols
    assert np.allclose(caffeine.geometry, qcio_structures.caffeine.geometry, rtol=1e-9)
    assert caffeine.multiplicity == qcio_structures.caffeine.multiplicity
    assert caffeine.charge == qcio_structures.caffeine.charge
    assert caffeine.identifiers.name == "caffeine"


def test_from_xyz_non_qcio_comments(test_data_dir):
    xyz_str = (test_data_dir / "caffeine.xyz").read_text()
    caffeine = Structure.from_xyz(xyz_str)
    assert caffeine.multiplicity == qcio_structures.caffeine.multiplicity
    assert caffeine.charge == qcio_structures.caffeine.charge
    assert caffeine.extras["xyz_comments"] == [
        "IUPAC",
        "1,3,7-trimethylpurine-2,6-dione",
    ]


def test_to_file_xyz(test_data_dir, tmp_path):
    caffeine = Structure.open(test_data_dir / "caffeine.xyz")
    caffeine.save(tmp_path / "caffeine_copy.xyz")
    caffeine_copy = Structure.open(tmp_path / "caffeine_copy.xyz")
    assert caffeine_copy.symbols == caffeine.symbols
    assert np.allclose(caffeine.geometry, qcio_structures.caffeine.geometry, rtol=1e-9)
    assert caffeine_copy.multiplicity == caffeine.multiplicity
    assert caffeine_copy.charge == caffeine.charge

    # single \n at end of file
    text = (tmp_path / "caffeine_copy.xyz").read_text()
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_to_xyz_comments(test_data_dir):
    caffeine = Structure.open(test_data_dir / "caffeine.xyz")
    xyz_str = caffeine.to_xyz()
    comments = xyz_str.split("\n")[1].split()
    assert "IUPAC" in comments
    assert "1,3,7-trimethylpurine-2,6-dione" in comments
    assert "qcio__identifiers_name=caffeine" in comments


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


def test_multi_xyz(test_data_dir):
    xyz_str = (test_data_dir / "multi.xyz").read_text()
    structures = Structure.from_xyz_multi(xyz_str)
    assert len(structures) == 2

    # Capturing comments correctly
    assert structures[0].identifiers.name == "caffeine"
    assert structures[0].charge == -1
    assert structures[1].extras[Structure._xyz_comment_key] == ["-107.04437987"]

    # Add space between structures
    xyz_lines = xyz_str.split("\n")
    xyz_lines.insert(26, "\n")
    xyz_str_with_space = "\n".join(xyz_lines)
    structures_space = Structure.from_xyz_multi(xyz_str_with_space)
    assert len(structures_space) == 2
    assert structures_space[0].identifiers.name == "caffeine"
    assert structures_space[0].charge == -1
    assert structures_space[1].extras[Structure._xyz_comment_key] == ["-107.04437987"]

    assert structures[0] == structures_space[0]
    assert structures[1] == structures_space[1]

    # Make sure it works on a single structure
    caffeine = Structure.open(test_data_dir / "caffeine.xyz")
    assert caffeine.symbols == qcio_structures.caffeine.symbols
    assert np.allclose(caffeine.geometry, qcio_structures.caffeine.geometry, rtol=1e-9)
    assert caffeine.multiplicity == qcio_structures.caffeine.multiplicity
    assert caffeine.charge == qcio_structures.caffeine.charge
    assert caffeine.identifiers.name == "caffeine"


def test_distance():
    struct = Structure(symbols=["H", "H"], geometry=[[0, 0, 0], [0, 0, 1]])
    assert struct.distance(0, 1) == 1.0

    struct = Structure(symbols=["H", "H"], geometry=[[0, 0, 0], [0, 0, -1]])
    assert struct.distance(0, 1) == 1.0

    struct = Structure(symbols=["H", "H"], geometry=[[0, 0, 0], [0, 1.4, -1.3]])

    assert struct.distance(0, 1) == pytest.approx(1.91049731, abs=1e-8)


def test_reorder_indices():
    struct = Structure(
        symbols=["H", "O", "H"], geometry=[[1, 0, 0], [0, 0, 0], [0, 0, 1]]
    )
    struct.swap_indices([(0, 1), (1, 2), (2, 0)])

    assert struct.symbols == ["H", "H", "O"]
    assert np.array_equal(struct.geometry, [[0, 0, 1], [1, 0, 0], [0, 0, 0]])
