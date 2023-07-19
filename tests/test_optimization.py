from qcio import OptimizationResults


def test_optimization_result_properties(sp_result):
    opt_res = OptimizationResults(
        trajectory=[sp_result],
    )

    assert opt_res.final_molecule == sp_result.input_data.molecule
    assert opt_res.energies == [sp_result.results.energy]
    assert opt_res.molecules == [sp_result.input_data.molecule]
