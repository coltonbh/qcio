import copy

import numpy as np
import pytest
from pydantic import ValidationError

from qcio import ConformerSearchResults, constants


def test_energies_size(water):
    """Test that the number of energies matches the number of conformers"""
    w1 = water
    w2 = copy.deepcopy(water)

    # No energies is fine
    ConformerSearchResults(
        conformers=[w1, w2],
    )

    # No energies is fine
    ConformerSearchResults(
        rotamers=[w1, w2],
    )

    with pytest.raises(ValidationError):
        ConformerSearchResults(
            conformers=[w1, w2],
            conformer_energies=[-1.0],
        )

    with pytest.raises(ValidationError):
        ConformerSearchResults(
            rotamers=[w1, w2],
            rotamer_energies=[-1.0, -2.0, -3.0],
        )


def test_relative_energies(water):
    w1 = water
    w2 = copy.deepcopy(water)
    w3 = copy.deepcopy(water)

    # No energies returns empty array
    csr = ConformerSearchResults(
        conformers=[w1, w2, w3],
    )

    np.testing.assert_array_equal(csr.conformer_energies_relative, np.array([]))

    # Energies are relative to the lowest energy
    csr = ConformerSearchResults(
        conformers=[w1, w2, w3],
        conformer_energies=[-1.0, -2.0, -3.0],
    )
    np.testing.assert_array_equal(
        csr.conformer_energies_relative, np.array([0.0, 1.0, 2.0])
    )

    # No energies returns empty array
    csr = ConformerSearchResults(
        rotamers=[w1, w2, w3],
    )

    np.testing.assert_array_equal(csr.conformer_energies_relative, np.array([]))

    # Energies are relative to the lowest energy
    csr = ConformerSearchResults(
        rotamers=[w1, w2, w3],
        rotamer_energies=[-1.0, -2.0, -3.0],
    )
    np.testing.assert_array_equal(
        csr.rotamer_energies_relative, np.array([0.0, 1.0, 2.0])
    )


def test_conformer_search_results_sorting(water):
    w1 = water
    w2 = copy.deepcopy(water)
    w3 = copy.deepcopy(water)

    csr = ConformerSearchResults(
        conformers=[w1, w2, w3],
        conformer_energies=[-1.0, -2.0, -3.0],
    )

    assert csr.conformers[0] is w3
    assert csr.conformers[1] is w2
    assert csr.conformers[2] is w1
    assert csr.conformer_energies.tolist() == [-3.0, -2.0, -1.0]


# Note: This test is slow since it uses RDKit's Heuckel method to determine connectivity
# and then uses the Hungarian algorithm to consider symmetries. If needed perhaps we can
# modify this test to run more quickly by changing the connectivity determination method
# and/or not considering symmetries.
def test_conformers_filtered(test_data_dir):
    # Catalyst/Na+ conformer search
    po_conf = ConformerSearchResults.open(test_data_dir / "conf_search.json")
    conf_filtered, energy_filtered = po_conf.conformers_filtered(
        threshold=0.47 * constants.ANGSTROM_TO_BOHR
    )
    assert len(conf_filtered) == 6
    selected = [0, 5, 7, 8, 9, 10]
    for i, conf in enumerate(conf_filtered):
        assert conf == po_conf.conformers[selected[i]]
        assert energy_filtered[i] == po_conf.conformer_energies_relative[selected[i]]
