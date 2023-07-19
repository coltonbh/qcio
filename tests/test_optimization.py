from qcio import OptimizationResults


def test_forward_refs_for_trajectory(sp_result):
    OptimizationResults(
        energies=[1.0],
        molecules=[sp_result.input_data.molecule],
        trajectory=[sp_result],
    )
