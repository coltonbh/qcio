"""Physical constants and periodic table from NIST CODATA 2022 and PubChem. All values
must have a reference to their source.

References:
    - <https://physics.nist.gov/cuu/Constants/Table/allascii.txt>
    - PubChem periodic table JSON: <https://pubchem.ncbi.nlm.nih.gov/periodic-table/>
"""

import csv
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

BOHR_TO_ANGSTROM = 0.529177210544
"""Conversion factor from Bohr to Angstrom. 

<https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0>
"""

ANGSTROM_TO_BOHR = 1 / BOHR_TO_ANGSTROM
"""Conversion factor from Angstrom to Bohr.

<https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0>
"""

HARTREE_TO_JOULE = 4.3597447222060e-18
"""Conversion factor from Hartree to Joule. 

<https://physics.nist.gov/cgi-bin/cuu/Value?na>
"""

AVOGADRO_NUMBER = 6.02214076e23
"""Avogadro's number. 

<https://physics.nist.gov/cuu/Constants/Table/allascii.txt>
"""

KCAL_TO_JOULE = 4.184e3
"""Conversion factor from kilocalorie to Joule.
Using kcal(th) as Therochemical calorie is the unit used in quantum chemistry.

<https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8>
"""

HARTREE_TO_KCAL_PER_MOL = HARTREE_TO_JOULE / KCAL_TO_JOULE * AVOGADRO_NUMBER
"""Conversion factor from Hartree to kcal/mol."""

_DATA_DIR = Path(__file__).parent / "constants_data"


class Atom(BaseModel):
    """Atom data model."""

    symbol: str
    number: int
    name: str
    mass: float
    group: Optional[int]
    period: int
    block: str
    electron_config: str


class PeriodicTable:
    """Periodic table data model. Data source and URL should be set by class methods."""

    # Should be set by @classmethod
    data_source: str = ""
    data_url: str = ""

    @classmethod
    def from_pubchem(cls):
        """Create a periodic table from PubChem data."""
        instance = cls()
        instance.data_source = "PubChem"
        instance.data_url = "https://pubchem.ncbi.nlm.nih.gov/periodic-table/"

        group_and_period_data = {}

        with open(_DATA_DIR / "group_period.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                group_and_period_data[row["Symbol"]] = {
                    "group": int(row["Group"]) if row["Group"] else None,
                    "period": int(row["Period"]),
                }

        with open(_DATA_DIR / "pubchem.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                symbol = row["Symbol"]
                atom = Atom(
                    symbol=symbol,
                    number=int(row["AtomicNumber"]),
                    name=row["Name"],
                    mass=float(row["AtomicMass"]),
                    group=group_and_period_data[symbol]["group"],
                    period=group_and_period_data[symbol]["period"],
                    block=row["GroupBlock"],
                    electron_config=row["ElectronConfiguration"],
                )
                setattr(instance, symbol, atom)
        return instance

    def group(self, group_number: int) -> List[Atom]:
        """Return all atoms in a group."""
        assert 1 <= group_number <= 18, "Group number must be between 1 and 18."
        return [
            atom
            for atom in self.__dict__.values()
            if isinstance(atom, Atom) and atom.group == group_number
        ]

    def period(self, period_number: int) -> List[Atom]:
        """Return all atoms in a period."""
        assert 1 <= period_number <= 7, "Period number must be between 1 and 7."
        return [
            atom
            for atom in self.__dict__.values()
            if isinstance(atom, Atom) and atom.period == period_number
        ]

    def number(self, number: int) -> Atom:
        """Return an atom by atomic number."""
        for atom in self.__dict__.values():
            if isinstance(atom, Atom) and atom.number == number:
                return atom
        raise ValueError(f"No atom with atomic number {number}.")


# ruff: noqa
periodic_table = PeriodicTable.from_pubchem()
"""Periodic table data from PubChem.

    Example:
        ```python
        >>> from qcio.constnats import periodic_table as pt
        
        >>> pt.Ni
        Atom(symbol='Ni', number=28, name='Nickel', mass=58.6934, group=10, period=4, block='d', electron_config='[Ar] 3d8 4s2')

        >>> pt.group(1)
        [Atom(symbol='H', number=1, name='Hydrogen', mass=1.00784, group=1, period=1, block='s', electron_config='1s1'),
        Atom(symbol='Li', number=3, name='Lithium', mass=6.94, group=1, period=2, block='s', electron_config='[He] 2s1'),
        Atom(symbol='Na', number=11, name='Sodium', mass=22.98976928, group=1, period=3, block='s', electron_config='[Ne] 3s1'),
        Atom(symbol='K', number=19, name='Potassium', mass=39.0983, group=1, period=4, block='s', electron_config='[Ar] 4s1'),
        Atom(symbol='Rb', number=37, name='Rubidium', mass=85.4678, group=1, period=5, block='s', electron_config='[Kr] 5s1'),
        Atom(symbol='Cs', number=55, name='Cesium', mass=132.90545196, group=1, period=6, block='s', electron_config='[Xe] 6s1'),
        Atom(symbol='Fr', number=87, name='Francium', mass=223.0, group=1, period=7, block='s', electron_config='[Rn] 7s1')]
        ```
"""
# ruff: noqa: enable

# https://depts.washington.edu/eooptic/linkfiles/dielectric_chart%5B1%5D.pdf
_SOLVENTS_DIELECTRIC = {
    "acetic acid": 6.15,
    "acetone": 20.7,
    "acetonitrile": 37.5,
    "anisole": 4.33,
    "benzene": 2.27,
    "bromobenzene": 5.17,
    "carbon disulfide": 2.6,
    "carbon tetrachloride": 2.24,
    "chlorobenzene": 5.62,
    "chloroform": 4.81,
    "cyclohexane": 2.02,
    "dibutyl ether": 3.1,
    "o -dichlorobenzene": 9.93,
    "1,2-dichloroethane": 10.36,
    "dichloromethane": 8.93,
    "diethylamine": 3.6,
    "diethyl ether": 4.33,
    "1,2-dimethoxyethane": 7.2,
    "n,n -dimethylacetamide": 37.8,
    "n,n -dimethylformamide": 36.7,
    "dimethyl sulfoxide": 46.7,
    "1,4-dioxane": 2.25,
    "ethanol": 24.5,
    "ethyl acetate": 6.02,
    "ethyl benzoate": 6.02,
    "formamide": 111,
    "hexamethylphosphoramide": 30,
    "isopropyl alcohol": 17.9,
    "methanol": 32.7,
    "2-methyl-2-propanol": 10.9,
    "nitrobenzene": 34.82,
    "nitromethane": 35.87,
    "pyridine": 12.4,
    "tetrahydrofuran": 7.58,
    "toluene": 2.38,
    "trichloroethylene": 3.4,
    "triethylamine": 2.42,
    "trifluoroacetic acid": 8.55,
    "2,2,2-trifluoroethanol": 8.55,
    "water": 80.1,
    "o -xylene": 2.57,
}
