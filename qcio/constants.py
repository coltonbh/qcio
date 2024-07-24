"""Physical constants and periodic table from NIST CODATA 2022. All values should have a
reference to their source.

References:
- https://physics.nist.gov/cuu/Constants/Table/allascii.txt
- PubChem periodic table JSON: https://pubchem.ncbi.nlm.nih.gov/periodic-table/
"""

import csv
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

# https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0
BOHR_TO_ANGSTROM = 0.529177210544
ANGSTROM_TO_BOHR = 1 / BOHR_TO_ANGSTROM
# https://www.physics.nist.gov/cgi-bin/cuu/Value?hr
HARTREE_TO_JOULE = 4.3597447222060e-18
# https://physics.nist.gov/cgi-bin/cuu/Value?na
AVOGADRO_NUMBER = 6.02214076e23
# https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8
# Using kcal(th) as Therochemical calorie is the unit used in quantum chemistry.
KCAL_TO_JOULE = 4.184e3
HARTREE_TO_KCAL_PER_MOL = HARTREE_TO_JOULE / KCAL_TO_JOULE * AVOGADRO_NUMBER

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


periodic_table = PeriodicTable.from_pubchem()

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
