from .models import Molecule

# Helper Molecules
water = Molecule(
    symbols=["O", "H", "H"],
    geometry=[0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0, 1.0, 0.0],
    charge=0,
    multiplicity=1,
)
