import timeit
from typing import Tuple

import numpy as np

from qcio import ProgramOutput, Structure, rmsd


def compute_rmsd(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """
    Compute the RMSD between two sets of coordinates.

    Parameters:
        coords1 (np.ndarray): An N x 3 array of coordinates.
        coords2 (np.ndarray): An N x 3 array of coordinates.

    Returns:
        float: The RMSD value.
    """
    # Ensure the arrays have the same shape
    assert coords1.shape == coords2.shape, "Coordinate arrays must be the same shape."

    # Compute the difference between the two arrays
    diff = coords1 - coords2
    # Sum squared differences for each atom (row) and average over all atoms
    rmsd_value = np.sqrt(np.mean(np.sum(diff**2, axis=1)))
    return rmsd_value


def kabsch(P: np.ndarray, Q: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the optimal rotation matrix that aligns P onto Q using the Kabsch algorithm.

    Parameters:
        P (np.ndarray): An N x 3 array of coordinates (the structure to rotate).
        Q (np.ndarray): An N x 3 array of coordinates (the reference structure).

    Returns:
        R (np.ndarray): The optimal 3x3 rotation matrix.
        centroid_P (np.ndarray): The centroid of P.
        centroid_Q (np.ndarray): The centroid of Q.
    """
    # Compute centroids
    centroid_P = np.mean(P, axis=0)
    centroid_Q = np.mean(Q, axis=0)

    # Center the coordinates
    P_centered = P - centroid_P
    Q_centered = Q - centroid_Q

    # Compute covariance matrix
    H = np.dot(P_centered.T, Q_centered)
    # Singular Value Decomposition
    U, S, Vt = np.linalg.svd(H)
    # Compute rotation matrix
    R = np.dot(Vt.T, U.T)

    # Correct for reflection (ensure a proper rotation with det(R)=1)
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = np.dot(Vt.T, U.T)

    return R, centroid_P, centroid_Q


def compute_rmsd_aligned(P: np.ndarray, Q: np.ndarray) -> float:
    """
    Compute the RMSD between two sets of coordinates after aligning P to Q using the Kabsch algorithm.

    Parameters:
        P (np.ndarray): An N x 3 array of coordinates (the structure to rotate).
        Q (np.ndarray): An N x 3 array of coordinates (the reference structure).

    Returns:
        float: The RMSD after optimal alignment.
    """
    # Compute the optimal rotation matrix and centroids
    R, centroid_P, centroid_Q = kabsch(P, Q)
    # Rotate P (after centering) and translate to the Q centroid
    P_aligned = np.dot(P - centroid_P, R.T) + centroid_Q
    # Compute the RMSD between the aligned coordinates and Q
    diff = P_aligned - Q
    rmsd_value = np.sqrt(np.mean(np.sum(diff**2, axis=1)))
    return rmsd_value


if __name__ == "__main__":
    import sys

    # Load structures
    s1 = Structure.open(sys.argv[1])
    s2 = Structure.open(sys.argv[2])
    rc_crest_dcm_frozen = ProgramOutput.open(
        "../../research/catalysis/data/2016-nat-chem/calcs/rc-dcm-hand-1-correct-freeze-ch2cl2-confsearch-nci-crest.json"
    )

    # Print RMSD values for correctness check
    print(f"my RMSD:    {compute_rmsd(s1.geometry, s2.geometry):.6f}")
    print(f"my RMSD aligned: {compute_rmsd_aligned(s1.geometry, s2.geometry):.6f}")
    print(f"rdkit RMSD: {rmsd(s1, s2, symmetry=False):.6f}")
    print(f"rdkit RMSD best: {rmsd(s1, s2, symmetry=True):.6f}")

    # # Define number of iterations and repeats
    NUMBER = 100  # how many times to run in each repeat
    REPEAT = 5  # number of repeats to collect statistics

    # Time the established rdkit RMSD function
    rdkit_timer = timeit.Timer(lambda: rmsd(s1, s2, symmetry=False))
    rdkit_times = rdkit_timer.repeat(repeat=REPEAT, number=NUMBER)

    # Time your custom compute_rmsd function
    mine_timer = timeit.Timer(lambda: compute_rmsd_aligned(s2.geometry, s1.geometry))
    mine_times = mine_timer.repeat(repeat=REPEAT, number=NUMBER)

    # Convert times to per-call timing (divide by NUMBER)
    rdkit_per_call = [t / NUMBER for t in rdkit_times]
    mine_per_call = [t / NUMBER for t in mine_times]

    # Print timing statistics
    print("\nTiming statistics (per call in seconds):")
    print("rdkit RMSD:")
    print(f"  min: {min(rdkit_per_call):.6f}")
    print(f"  max: {max(rdkit_per_call):.6f}")
    print(f"  avg: {np.mean(rdkit_per_call):.6f}")

    print("my RMSD:")
    print(f"  min: {min(mine_per_call):.6f}")
    print(f"  max: {max(mine_per_call):.6f}")
    print(f"  avg: {np.mean(mine_per_call):.6f}")

    # Print speedup factor
    speedup = np.mean(rdkit_per_call) / np.mean(mine_per_call)
    print(f"\nSpeedup factor: {speedup:.2f}")
