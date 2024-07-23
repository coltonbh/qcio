from qcio import OptimizationResults, ProgramInput, ProgramOutput
from qcio.view import generate_optimization_plot


def test_generate_optimization_plot_with_single_prog_output_failure(
    prog_input, prog_output_failure
):
    opt_input = prog_input("optimization")

    prog_output = ProgramOutput[ProgramInput, OptimizationResults](
        input_data=opt_input,
        success=False,
        traceback="Traceback...",
        results=OptimizationResults(trajectory=[prog_output_failure]),
        provenance={"program": "fake-program"},
    )
    generate_optimization_plot(prog_output)
