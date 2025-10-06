from qcio import OptimizationData


def test_optimization_result_properties(results):
    opt_res = OptimizationData(
        trajectory=[results],
    )

    # Test properties
    assert opt_res.final_structure == results.input_data.structure
    assert opt_res.energies == [results.data.energy]
    assert opt_res.structures == [results.input_data.structure]
    # Test custom __repr_args__
    repr_args = opt_res.__repr_args__()
    assert isinstance(repr_args, list)
    for arg in repr_args:
        assert isinstance(arg, tuple)
        assert len(arg) == 2
        assert isinstance(arg[0], str)
        assert isinstance(arg[1], str)


def test_optimization_save_to_xyz(results, tmp_path):
    opt_res = OptimizationData(
        trajectory=[results] * 3,
    )
    opt_res.save(tmp_path / "opt_res.xyz")

    text = (tmp_path / "opt_res.xyz").read_text()
    # Text must be de-dented exactly as below
    correct_text = """3
qcio_charge=0 qcio_multiplicity=1 qcio__identifiers_name=water
O  0.01340919176202180 0.01026321207824930 -0.00368477733600419
H  0.12112430307330672 0.97600619725464122 0.08599884278042236
H  0.75016279902412597 -0.33132205318865016 -0.54481406902570462
3
qcio_charge=0 qcio_multiplicity=1 qcio__identifiers_name=water
O  0.01340919176202180 0.01026321207824930 -0.00368477733600419
H  0.12112430307330672 0.97600619725464122 0.08599884278042236
H  0.75016279902412597 -0.33132205318865016 -0.54481406902570462
3
qcio_charge=0 qcio_multiplicity=1 qcio__identifiers_name=water
O  0.01340919176202180 0.01026321207824930 -0.00368477733600419
H  0.12112430307330672 0.97600619725464122 0.08599884278042236
H  0.75016279902412597 -0.33132205318865016 -0.54481406902570462
"""
    assert text == correct_text


def test_optimization_save_non_xyz(results, tmp_path):
    opt_res = OptimizationData(
        trajectory=[results] * 3,
    )
    opt_res.save(tmp_path / "opt_res.json")
    opt_res_copy = OptimizationData.open(tmp_path / "opt_res.json")
    assert opt_res == opt_res_copy
