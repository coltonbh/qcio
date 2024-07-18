"""
Tools for visualizing qcio objects in Jupyter Notebooks.

Design Decisions:
    - The view function is the top-level method for viewing all qcio objects. It can 
        accept one or many objects and will determine the appropriate viewer to use.
    - All functions that begin with "generate" will return a string of HTML. If users
        want to use this HTML to create a custom view, they can do so. If they want to
        display the HTML in a Jupyter Notebook, they can call display(HTML(html_string))
        after importing `from IPython.display import HTML, display`.
    - The basic layout for viewing results (all ProgramOutput objects) is a table of
        basic parameters followed by a structure viewer and results table or plot.
        DualProgramInputs add details for the subprogram.
        ----------------------------------------------------------------------------
        | Structure Name | Success | Calculation Type | Program | Model | Keywords |
        ----------------------------------------------------------------------------
        |                                    |                                     |
        |      Structure Viewer (Optional)   |        Results Table or Plot        | 
        |                                    |                                     |
        ----------------------------------------------------------------------------
"""

import base64
import html
import io
from contextlib import contextmanager
from itertools import zip_longest
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import py3Dmol as p3d
from IPython.display import HTML, display

from qcio import (
    DualProgramInput,
    OptimizationResults,
    ProgramInput,
    ProgramOutput,
    SinglePointResults,
    Structure,
    constants,
)


def generate_structure_viewer_html(
    struct: Union[Structure, List[Structure]],
    *,
    width: int = 600,
    height: int = 450,
    style: Optional[Dict] = None,
    show_indices: bool = False,
    png: bool = False,
    **kwargs,
) -> str:
    """
    Generate the core HTML viewer for a Structure or list of Structures using py3Dmol.

    Args:
        struct: The Structure or list of Structures to visualize. Lists will be
            animated.
        width: The width of the viewer in pixels.
        height: The height of the viewer in pixels.
        style: A dictionary of styles to apply to the viewer.
        show_indices: Whether to show the atom indices in the viewer.
        png: Whether to return a PNG image of the viewer instead of the WebGL HTML.

    Returns:
        str: The HTML string for the viewer.
    """
    viewer = p3d.view(width=width, height=height)
    if isinstance(struct, list):
        combined_xyz = "".join(s.to_xyz() for s in struct)
        viewer.addModelsAsFrames(combined_xyz, "xyz")
        viewer.animate({"loop": "forward"})
    else:
        viewer.addModel(struct.to_xyz(), "xyz")

    struct = struct[-1] if isinstance(struct, list) else struct

    if show_indices:
        for j, (symbol, coord) in enumerate(
            zip(struct.symbols, struct.geometry * constants.BOHR_TO_ANGSTROM)
        ):
            viewer.addLabel(
                str(j),
                {
                    "position": {"x": coord[0], "y": coord[1], "z": coord[2]},
                    "style": {"fontColor": "black", "backgroundColor": "white"},
                },
            )

    viewer.setStyle(style or {"stick": {}, "sphere": {"scale": 0.3}})
    viewer.zoomTo()

    return (
        viewer.write_html()
        if not png
        else NotImplementedError("PNG generation is not yet implemented.")
    )


def generate_structure_html(
    struct: Union[Structure, List[Structure]],
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    title_extra: Optional[str] = None,
    subtitle_extra: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Generate an HTML viewer with an optional title and/or subtitle for a Structure or
    list of Structures using py3Dmol.

    Args:
        struct: The Structure or list of Structures to visualize. Lists will be
            animated.
        title: The title to display above the viewer.
        subtitle: The subtitle to display below the viewer.
        title_extra: Extra text to display after the title.
        subtitle_extra: Extra text to display after the subtitle.
        **kwargs: Additional keyword arguments to pass to
            generate_structure_viewer_html.

    Returns:
        str: The HTML string for the viewer with optional titles and subtitles.
    """
    mol_viewer_html = generate_structure_viewer_html(struct, **kwargs)
    struct = struct[0] if isinstance(struct, list) else struct

    title = f"{title or struct.ids.name or struct.ids.smiles or ''}"
    title_extra = f"{title_extra or ''}"
    subtitle = f"{subtitle or ''}"
    subtitle_extra = f"{subtitle_extra or ''}"

    return f""" 
        <div style="text-align: center;">
            <h3>{title} {title_extra}</h3>
            {mol_viewer_html}
            <h4>{subtitle} {subtitle_extra}</h4>
        </div>
    """


def generate_dictionary_string(dictionary: Dict[str, Any]) -> str:
    """
    Generate an HTML string displaying a dictionary without explicit row colors.

    Args:
        dictionary: The dictionary to display.

    Returns:
        str: A string of HTML displaying the dictionary with each key/value pair on a
            new line.
    """
    rows = "".join(
        f"<tr><td class='key'>{key}</td><td class='value'>{value}</td></tr>"
        for key, value in dictionary.items()
    )
    return f"<table class='inner-table'>{rows}</table>"


def generate_files_string(files: Dict[str, Union[str, bytes]]) -> str:
    """
    Generate an HTML string displaying a dictionary of files substituting <str> or
    <bytes> for the actual file data
    """
    # Generate the symbolic dictionary
    viewer_dict = {}
    for key, value in files.items():
        if isinstance(value, bytes):
            viewer_dict[key] = html.escape("<bytes>")
        elif isinstance(value, str):
            viewer_dict[key] = html.escape("<str>")

    return generate_dictionary_string(viewer_dict)


def generate_output_table(*prog_outputs: ProgramOutput) -> str:
    """
    Generate an HTML table displaying the basic parameters for ProgramOutput objects.

    Args:
        *prog_outputs: The ProgramOutput objects to display.

    Returns:
        str: A string of HTML displaying the ProgramOutput objects in a table.
    """
    styles = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }
        .inner-table {
            border: none;
            width: 100%;
        }
        .inner-table td {
            border: none;
            padding: 2px 5px;
        }
        .key, .value {
            text-align: left;
            white-space: nowrap;
        }
    </style>
    """

    table_header = """
    <table>
        <tr>
            <th>Structure Name</th>
            <th>Success</th>
            <th>Calculation Type</th>
            <th>Program</th>
            <th>Model</th>
            <th>Keywords</th>
    """
    if any(po.input_data.files for po in prog_outputs):
        table_header += "<th>Input Files</th>"

    if any(isinstance(po.input_data, DualProgramInput) for po in prog_outputs):
        table_header += """
            <th>Subprogram</th>
            <th>Subprogram Model</th>
            <th>Subprogram Keywords</th>
        """
    table_header += "</tr>"

    table_rows = []
    for po in prog_outputs:
        success_style = (
            'style="color: green; font-weight: bold;"'
            if po.success
            else 'style="color: red; font-weight: bold;"'
        )
        base_row = f"""
        <tr>
            <td>{po.input_data.structure.ids.name}</td>
            <td {success_style}>{po.success}</td>
            <td>{po.input_data.calctype.name}</td>
            <td>{f"{po.provenance.program} {po.provenance.program_version or ''}"}</td>
            <td>{po.input_data.model}</td>
            <td>{generate_dictionary_string(po.input_data.keywords)}</td>
        """
        if po.input_data.files:
            base_row += f"<td>{generate_files_string(po.input_data.files)}</td>"

        if isinstance(po.input_data, DualProgramInput):
            base_row += f"""
            <td>{po.input_data.subprogram}</td>
            <td>{po.input_data.subprogram_args.model}</td>
            <td>{generate_dictionary_string(po.input_data.subprogram_args.keywords)}</td>
            """
        base_row += "</tr>"
        table_rows.append(base_row)

    table_footer = "</table>"
    return styles + table_header + "\n".join(table_rows) + table_footer


def generate_optimization_plot(
    prog_output: ProgramOutput, figsize=(6.4, 4.8), grid=True
) -> str:
    """
    Generate a plot of the energy optimization by cycle for a single ProgramOutput.

    Args:
        prog_output: The ProgramOutput to generate the plot for.
        figsize: The size of the figure in inches.
        grid: Whether to display grid lines on the plot.

    Returns:
        str: A string of HTML displaying the plot as a png image encoded in base64.
    """
    energies = prog_output.results.energies * constants.HARTREE_TO_KCAL_PER_MOL
    baseline_energy = energies[0]
    relative_energies = energies - baseline_energy
    last_is_nan = np.isnan(relative_energies[-1])

    if last_is_nan:
        delta_E = relative_energies[-2]
    else:
        delta_E = relative_energies[-1]

    fig, ax1 = plt.subplots(figsize=figsize)
    color = "tab:blue"
    ax1.set_xlabel("Optimization Cycle")
    ax1.set_ylabel("Relative Energy (kcal/mol)", color=color)
    ax1.plot(relative_energies, label="Energy", marker="o", color="green")
    if last_is_nan:
        ax1.plot(
            len(relative_energies) - 1, relative_energies[-2], marker="x", color="red"
        )
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.text(
        0.95,
        0.85,
        f"ΔE = {delta_E:.2f} kcal/mol",
        verticalalignment="top",
        horizontalalignment="right",
        transform=ax1.transAxes,
        color="black",
        fontsize=14,
    )
    plt.title("Energy Optimization by Cycle", pad=20)
    ax1.legend(loc="upper right")
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)  # Close the figure to avoid duplicate plots
    return (
        f'<img src="data:image/png;base64,{image_base64}" alt="Energy Optimization by '
        'Cycle" style="width: 100%; max-width: 600px;">'
    )


@contextmanager
def _numpy_print_options(*args, **kwargs):
    """
    Temporarily set numpy print options.

    Args:
        *args: Arguments for numpy print options.
        **kwargs: Keyword arguments for numpy print options.
    """
    original_options = np.get_printoptions()
    np.set_printoptions(*args, **kwargs)
    try:
        yield
    finally:
        np.set_printoptions(**original_options)


def _not_empty(value) -> bool:
    """
    Check if a value is empty. Accommodates numpy arrays.

    Args:
        value: The value to check.

    Returns:
        bool: True if the value is not empty, False otherwise.
    """
    if isinstance(value, np.ndarray):
        return bool(value.any())
    return bool(value)


def generate_results_table(results: SinglePointResults) -> str:
    """
    Generate an HTML table displaying the results.

    Args:
        results: The Results object to display.

    Returns:
        str: A string of HTML displaying the results in a table.
    """

    rows = ""
    for key, value in results.__dict__.items():
        if _not_empty(value):
            if key != "files":
                with _numpy_print_options(
                    threshold=10,
                    formatter={"float_kind": "{:0.2e}".format},
                ):
                    rows += f"<tr><td>{key}</td><td>{value}</td></tr>"

    # Add the files to the bottom table
    if _not_empty(results.files):
        rows += (
            f"<tr><td>Files</td><td>{generate_files_string(results.files)}</td></tr>"
        )

    return f"""
    <table style="width: 100%; border-collapse: collapse; text-align: left;">
        <thead>
            <tr>
                <th style="border: 1px solid black; padding: 8px;">Result</th>
                <th style="border: 1px solid black; padding: 8px;">Value</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """


def structures(
    *structures: Structure,
    titles: Optional[List[str]] = None,
    subtitles: Optional[List[str]] = None,
    width: int = 600,
    height: int = 450,
    show_indices: bool = False,
    **kwargs,
) -> None:
    """
    Display one or many Structure objects.

    Args:
        *structures: The Structure objects to display.
        titles: The titles to display above the structures.
        subtitles: The subtitles to display below the structures.
        width: The width of the structure viewer in pixels.
        height: The height of the structure viewer in pixels.
        show_indices: Whether to show the atom indices in the viewer.
        **kwargs: Additional keyword arguments to pass to the viewer functions.

    Returns:
        None. Displays the structures in the Jupyter Notebook.
    """
    titles = titles or []
    subtitles = subtitles or []
    final_html = []

    for i, (struct, title, subtitle) in enumerate(
        zip_longest(structures, titles, subtitles)
    ):
        if i % 2 == 0:
            if i != 0:
                final_html.append("</div>")
            final_html.append(
                '<div style="display: flex; align-items: center; justify-content: center;">'  # noqa
            )

        final_html.append(
            generate_structure_html(
                struct,
                width=width,
                height=height,
                title=title,
                subtitle=subtitle,
                show_indices=show_indices,
                **kwargs,
            )
        )

    if len(structures) % 2 != 0:
        final_html.append("</div>")

    display(HTML("".join(final_html)))


def program_outputs(
    *prog_outputs: ProgramOutput[
        Union[ProgramInput, DualProgramInput], OptimizationResults
    ],
    width: int = 600,
    height: int = 450,
    animate: bool = True,
    show_indices: bool = False,
    struct_viewer: bool = True,
    **kwargs,
) -> None:
    """
    Display one or many ProgramOutput objects.

    Args:
        *prog_outputs: The ProgramOutput objects to display.
        width: The width of the structure and plot viewer in pixels.
        height: The height of the structure and plot viewer in pixels.
        animate: Whether to animate the structure if it is an optimization.
        show_indices: Whether to show the atom indices in the viewer.
        **kwargs: Additional keyword arguments to pass to the viewer functions.

    Returns:
        None. Displays the ProgramOutput objects in the Jupyter Notebook.
    """
    titles = kwargs.get("titles") or []
    subtitles = kwargs.get("subtitles") or []

    final_html = []
    for po, title, subtitle in zip_longest(prog_outputs, titles, subtitles):
        final_html.append(generate_output_table(po))

        # Create structure viewer
        if not struct_viewer:
            structure_html = "struct_viewer = False"

        else:
            # Determine the structure to use
            title_extra = ""
            if isinstance(po.results, OptimizationResults):
                for_viewer: Union[Structure, List[Structure]]
                if animate:
                    for_viewer = po.results.structures
                else:
                    for_viewer = po.results.final_structure
                    title_extra = "(Final Structure)"
            else:
                for_viewer = po.input_data.structure

            structure_html = generate_structure_html(
                for_viewer,
                title=title,
                title_extra=title_extra,
                subtitle=subtitle,
                show_indices=show_indices,
                **kwargs,
            )

        # Create results table or plot
        if isinstance(po.results, OptimizationResults):
            results_html = generate_optimization_plot(
                po, figsize=(width / 100, height / 100)
            )
        else:
            results_html = generate_results_table(po.results)

        final_html.append(
            f"""
    <div style="text-align: center;">
        <div style="display: flex; align-items: center; justify-content: space-around;">
            <div style="text-align: center; margin-right: 20px; flex: 1;">
                <div style="display: inline-block; text-align: center;">
                    {structure_html}
                </div>
            </div>
            <div style="text-align: center; margin-left: 20px; flex: 1;">
                {results_html}
            </div>
        </div>
    </div>
            """
        )

    display(HTML("".join(final_html)))


def view(
    *objs: Union[ProgramOutput, Structure],
    titles: Optional[List[str]] = None,
    subtitles: Optional[List[str]] = None,
    **kwargs,
) -> None:
    """
    Top level method for viewing all qcio objects.

    Args:
        *objs: The ProgramOutput objects to view. May pass one or more objects.
        titles: The titles to display above the structures.
        subtitles: The subtitles to display below the structures.
        **kwargs: Additional keyword arguments to pass to the viewer functions.

    Returns:
        None. Displays the qcio objects in the Jupyter Notebook.
    """
    titles = titles or []
    subtitles = subtitles or []

    if len(titles) > len(objs):
        raise ValueError("Number of titles exceeds number of objects.")
    if len(subtitles) > len(objs):
        raise ValueError("Number of subtitles exceeds number of objects.")

    if all(isinstance(obj, Structure) for obj in objs):
        structures(*objs, titles=titles, subtitles=subtitles, **kwargs)  # type: ignore

        return

    for obj, title, subtitle in zip_longest(objs, titles, subtitles):
        _titles = [title] if title else None
        _subtitles = [subtitle] if subtitle else None

        if isinstance(obj, Structure):
            structures(obj, titles=_titles, subtitles=_subtitles, **kwargs)
        elif isinstance(obj, ProgramOutput):
            program_outputs(obj, titles=_titles, subtitles=_subtitles, **kwargs)
        else:
            raise NotImplementedError(f"Viewing of {type(obj)} is not implemented.")
