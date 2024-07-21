import pytest

from qcio.constants import PeriodicTable
from qcio.constants import periodic_table as pt


def test_periodic_table_from_pubchem():
    pt = PeriodicTable.from_pubchem()
    assert pt.data_source == "PubChem"
    assert pt.data_url == "https://pubchem.ncbi.nlm.nih.gov/periodic-table/"


def test_group_period_lookup_params():
    with pytest.raises(AssertionError):
        pt.group(0)
    with pytest.raises(AssertionError):
        pt.group(19)
    with pytest.raises(AssertionError):
        pt.period(0)
    with pytest.raises(AssertionError):
        pt.period(8)


def test_group_and_period_data():
    # Assert that all groups and periods are correct
    assert [a.symbol for a in pt.group(1)] == ["H", "Li", "Na", "K", "Rb", "Cs", "Fr"]
    assert [a.symbol for a in pt.group(2)] == ["Be", "Mg", "Ca", "Sr", "Ba", "Ra"]
    assert [a.symbol for a in pt.group(3)] == ["Sc", "Y", "Lu", "Lr"]
    assert [a.symbol for a in pt.group(4)] == ["Ti", "Zr", "Hf", "Rf"]
    assert [a.symbol for a in pt.group(5)] == ["V", "Nb", "Ta", "Db"]
    assert [a.symbol for a in pt.group(6)] == ["Cr", "Mo", "W", "Sg"]
    assert [a.symbol for a in pt.group(7)] == ["Mn", "Tc", "Re", "Bh"]
    assert [a.symbol for a in pt.group(8)] == ["Fe", "Ru", "Os", "Hs"]
    assert [a.symbol for a in pt.group(9)] == ["Co", "Rh", "Ir", "Mt"]
    assert [a.symbol for a in pt.group(10)] == ["Ni", "Pd", "Pt", "Ds"]
    assert [a.symbol for a in pt.group(11)] == ["Cu", "Ag", "Au", "Rg"]
    assert [a.symbol for a in pt.group(12)] == ["Zn", "Cd", "Hg", "Cn"]
    assert [a.symbol for a in pt.group(13)] == ["B", "Al", "Ga", "In", "Tl", "Nh"]
    assert [a.symbol for a in pt.group(14)] == ["C", "Si", "Ge", "Sn", "Pb", "Fl"]
    assert [a.symbol for a in pt.group(15)] == ["N", "P", "As", "Sb", "Bi", "Mc"]
    assert [a.symbol for a in pt.group(16)] == ["O", "S", "Se", "Te", "Po", "Lv"]
    assert [a.symbol for a in pt.group(17)] == ["F", "Cl", "Br", "I", "At", "Ts"]
    assert [a.symbol for a in pt.group(18)] == [
        "He",
        "Ne",
        "Ar",
        "Kr",
        "Xe",
        "Rn",
        "Og",
    ]

    assert [a.symbol for a in pt.period(1)] == ["H", "He"]
    assert [a.symbol for a in pt.period(2)] == [
        "Li",
        "Be",
        "B",
        "C",
        "N",
        "O",
        "F",
        "Ne",
    ]
    assert [a.symbol for a in pt.period(3)] == [
        "Na",
        "Mg",
        "Al",
        "Si",
        "P",
        "S",
        "Cl",
        "Ar",
    ]
    assert [a.symbol for a in pt.period(4)] == [
        "K",
        "Ca",
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Ga",
        "Ge",
        "As",
        "Se",
        "Br",
        "Kr",
    ]
    assert [a.symbol for a in pt.period(5)] == [
        "Rb",
        "Sr",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "In",
        "Sn",
        "Sb",
        "Te",
        "I",
        "Xe",
    ]
    assert [a.symbol for a in pt.period(6)] == [
        "Cs",
        "Ba",
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
        "Tl",
        "Pb",
        "Bi",
        "Po",
        "At",
        "Rn",
    ]
    assert [a.symbol for a in pt.period(7)] == [
        "Fr",
        "Ra",
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
        "Am",
        "Cm",
        "Bk",
        "Cf",
        "Es",
        "Fm",
        "Md",
        "No",
        "Lr",
        "Rf",
        "Db",
        "Sg",
        "Bh",
        "Hs",
        "Mt",
        "Ds",
        "Rg",
        "Cn",
        "Nh",
        "Fl",
        "Mc",
        "Lv",
        "Ts",
        "Og",
    ]
