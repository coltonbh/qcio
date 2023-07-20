from qcio import OptimizationResults


def test_optimization_result_properties(sp_output):
    opt_res = OptimizationResults(
        trajectory=[sp_output],
    )

    # Test properties
    assert opt_res.final_molecule == sp_output.input_data.molecule
    assert opt_res.energies == [sp_output.results.energy]
    assert opt_res.molecules == [sp_output.input_data.molecule]
    # Test custom __repr_args__
    repr_args = opt_res.__repr_args__()
    assert isinstance(repr_args, list)
    for arg in repr_args:
        assert isinstance(arg, tuple)
        assert len(arg) == 2
        assert isinstance(arg[0], str)
        assert isinstance(arg[1], str)
