from qcio import OptimizationResults


def test_optimization_result_properties(prog_output):
    opt_res = OptimizationResults(
        trajectory=[prog_output],
    )

    # Test properties
    assert opt_res.final_molecule == prog_output.input_data.molecule
    assert opt_res.energies == [prog_output.results.energy]
    assert opt_res.molecules == [prog_output.input_data.molecule]
    # Test custom __repr_args__
    repr_args = opt_res.__repr_args__()
    assert isinstance(repr_args, list)
    for arg in repr_args:
        assert isinstance(arg, tuple)
        assert len(arg) == 2
        assert isinstance(arg[0], str)
        assert isinstance(arg[1], str)


def test_optimization_save_to_xyz(prog_output, tmp_path):
    opt_res = OptimizationResults(
        trajectory=[prog_output] * 3,
    )
    opt_res.save(tmp_path / "opt_res.xyz")

    text = (tmp_path / "opt_res.xyz").read_text()
    # Text must be dedented exactly as below
    correct_text = """3
qcio_charge=0 qcio_multiplicity=1
O      0.000000000000     0.000000000000     0.000000000000
H      0.000000000000     0.000000000000     0.529177210903
H      0.000000000000     0.529177210903     0.000000000000
3
qcio_charge=0 qcio_multiplicity=1
O      0.000000000000     0.000000000000     0.000000000000
H      0.000000000000     0.000000000000     0.529177210903
H      0.000000000000     0.529177210903     0.000000000000
3
qcio_charge=0 qcio_multiplicity=1
O      0.000000000000     0.000000000000     0.000000000000
H      0.000000000000     0.000000000000     0.529177210903
H      0.000000000000     0.529177210903     0.000000000000
"""
    assert text == correct_text


def test_optimization_save_non_xyz(prog_output, tmp_path):
    opt_res = OptimizationResults(
        trajectory=[prog_output] * 3,
    )
    opt_res.save(tmp_path / "opt_res.json")
    opt_res_copy = OptimizationResults.open(tmp_path / "opt_res.json")
    assert opt_res == opt_res_copy
