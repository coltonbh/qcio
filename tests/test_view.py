from qcio import CalcSpec, OptimizationData, Results
from qcio.view import generate_optimization_plot


def test_generate_optimization_plot_with_single_prog_output_failure(
    calc_input, results_failure
):
    opt_input = calc_input("optimization")

    prog_output = Results[CalcSpec, OptimizationData](
        input_data=opt_input,
        success=False,
        traceback="Traceback...",
        data=OptimizationData(trajectory=[results_failure]),
        provenance={"program": "fake-program"},
    )
    generate_optimization_plot(prog_output)
