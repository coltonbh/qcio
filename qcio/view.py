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
        | Structure      | Success | Calculation Type | Program | Model | Keywords |
        ----------------------------------------------------------------------------
        |                                    |                                     |
        |      Structure Viewer (Optional)   |        Results Table or Plot        | 
        |                                    |                                     |
        ----------------------------------------------------------------------------
"""

import base64
import html
import io
import math
from contextlib import contextmanager
from itertools import zip_longest
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from qcio import (
    ConformerSearchResults,
    DistanceUnits,
    DualProgramInput,
    Files,
    OptimizationResults,
    ProgramInput,
    ProgramOutput,
    Results,
    SinglePointResults,
    Structure,
    constants,
)

# View dependencies
try:
    import matplotlib.pyplot as plt
    import py3Dmol as p3d
    from IPython.display import HTML, display
    from rdkit import Chem
    from rdkit.Chem import Draw
except ImportError as e:
    missing_packages = []
    if "matplotlib" in str(e):
        missing_packages.append("matplotlib")
    if "py3Dmol" in str(e):
        missing_packages.append("py3Dmol")
    if "IPython" in str(e):
        missing_packages.append("IPython")
    if "rdkit" in str(e):
        missing_packages.append("rdkit")
    raise ImportError(
        f"Missing dependencies: {', '.join(missing_packages)} required for the view "
        "module. Please install them using: pip install qcio[view]"
    )

DEFAULT_WIDTH: int = 600
"""The default width of the viewer in pixels."""
DEFAULT_HEIGHT: int = 450
"""The default height of the viewer in pixels."""


def generate_structure_viewer_html(
    *structs: Union["Structure", List["Structure"]],
    width: Optional[int] = None,
    height: Optional[int] = None,
    titles: Optional[List[str]] = None,
    subtitles: Optional[List[str]] = None,
    titles_extra: Optional[List[str]] = None,
    subtitles_extra: Optional[List[str]] = None,
    distances: Optional[List[Tuple[int, int]]] = None,
    distance_units: DistanceUnits = DistanceUnits.bohr,
    style: Optional[Dict] = None,
    show_indices: bool = False,
    same_viewer: bool = False,
    view_2d: bool = False,
    interval: int = 100,
) -> str:
    """
    Generate the core HTML viewer for a Structure or list of Structures using py3Dmol
    or 2D PNG images. These keywords may be passed to high level viewer functions.

    Args:
        structs: The Structure or list of Structures to visualize.
        width: The width of the viewer in pixels. Defaults to 600.
        height: The height of the viewer in pixels. Defaults to 450.
        titles: The titles to display above the viewer. Will default to the Structure
            name or SMILES if not provided.
        subtitles: The subtitles to display below the viewer.
        titles_extra: Extra text to display after the title. This is useful for adding
            additional context to a default title.
        subtitles_extra: Extra text to display after the subtitle. Useful for adding
            text after an autogenerated subtitle such as relative energy.
        distances: A list of tuples of atom indices to display distances between.
        distance_units: The units to display the distances in. Defaults to bohr. May
            pass 'angstrom' to display in angstroms.
        style: A dictionary of styles to apply to the viewer (for py3Dmol). Should be a
            dictionary for AtomStyleSpec <https://3dmol.org/doc/AtomStyleSpec.html>
        show_indices: Whether to show the atom indices in the viewer.
        view_2d: Whether to display the structure in 2D (PNG images).
        interval: The interval in milliseconds for the animation.

    Returns:
        str: The HTML string for the viewer.

    Raises:
        ValueError: If a list of Structures is passed and view_2d is True.
    """

    # Set defaults
    width = width or DEFAULT_WIDTH
    height = height or DEFAULT_HEIGHT

    titles = titles or []
    subtitles = subtitles or []
    titles_extra = titles_extra or []
    subtitles_extra = subtitles_extra or []

    # Start HTML with flex container
    html_parts = [
        '<div style="display: flex; flex-wrap: wrap; justify-content: center;">'
    ]

    if not view_2d:
        # Create the viewer
        if len(structs) == 1 or same_viewer:
            viewer = p3d.view(width=width, height=height, viewergrid=(1, 1))
        else:
            # Determine the number of rows needed for multiple structures
            rows = math.ceil(len(structs) / 2)
            viewer = p3d.view(
                width=width * 2,
                height=height * rows,
                linked=False,
                viewergrid=(rows, 2),
            )

    for i, (struct, title, subtitle, title_extra, subtitle_extra) in enumerate(
        zip_longest(structs, titles, subtitles, titles_extra, subtitles_extra)
    ):
        # Set the title and subtitle
        if isinstance(struct, list):
            name = struct[0].ids.name
            smiles = struct[0].ids.smiles
        else:
            name = struct.ids.name
            smiles = struct.ids.smiles

        title = f"{title or name or smiles or ''}"
        title_extra = f"{title_extra or ''}"
        subtitle = f"{subtitle or ''}"
        subtitle_extra = f"{subtitle_extra or ''}"

        if view_2d:
            if isinstance(struct, list):
                raise ValueError(
                    "Cannot display multiple 2D structures in one viewer. Do not submit"
                    " Structures in a list. If you want to view multiple structures, "
                    "unpack your list with *my_list_of_structures."
                )
            adjusted_width, adjusted_height = int(width * 0.75), int(height * 0.75)
            mol = Chem.MolFromSmiles(struct.ids.smiles or struct.to_smiles())
            img = Draw.MolToImage(mol, size=(adjusted_width, adjusted_height))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_str = base64.b64encode(buf.getvalue()).decode("utf-8")

            html_parts.append(
                f'<div style="margin: 10px; text-align: center; padding: 15px; width: '
                f'{adjusted_width}px; height: {adjusted_height + 60}px;">'
                f"<h2>{title} {title_extra}</h2>"
                f'<img src="data:image/png;base64,{img_str}" width="{adjusted_width}" '
                f'height="{adjusted_height}"/>'
                f"<h4>{subtitle} {subtitle_extra}</h4>"
                f"</div>"
            )
        else:
            if same_viewer:
                grid = (0, 0)
            else:
                grid = divmod(i, 2)

            if isinstance(struct, list):  # Animate lists of structures
                combined_xyz = "".join(s.to_xyz() for s in struct)
                viewer.addModelsAsFrames(combined_xyz, "xyz", viewer=grid)
                viewer.animate({"loop": "forward", "interval": interval}, viewer=grid)
                # viewer.animate({"loop": "forward"}, viewer=grid)
            else:
                viewer.addModel(struct.to_xyz(), "xyz", viewer=grid)

            viewer.addLabel(
                f"{title} {title_extra}",
                {
                    "position": {"x": width / 2, "y": 0, "z": 0},
                    "alignment": "topCenter",
                    "fontSize": 24,
                    "backgroundOpacity": 0,
                    "fontColor": "black",
                    "useScreen": True,
                },
                viewer=grid,
            )

            viewer.addLabel(
                f"{subtitle} {subtitle_extra}",
                {
                    "position": {"x": width / 2, "y": height, "z": 0},
                    "alignment": "bottomCenter",
                    "fontSize": 20,
                    "backgroundOpacity": 0,
                    "fontColor": "black",
                    "useScreen": True,
                },
                viewer=grid,
            )
            if distances:
                assert isinstance(
                    struct, Structure
                ), "Displaying distances for lists of structures is not yet implemented"
                for atom1, atom2 in distances:
                    a1_coords = struct.geometry_angstrom[atom1]
                    a2_coords = struct.geometry_angstrom[atom2]
                    # Add line between the two atoms
                    viewer.addLine(
                        {
                            "start": {
                                "x": a1_coords[0],
                                "y": a1_coords[1],
                                "z": a1_coords[2],
                            },
                            "end": {
                                "x": a2_coords[0],
                                "y": a2_coords[1],
                                "z": a2_coords[2],
                            },
                            "color": "red",
                            "linewidth": 2,
                        },
                        viewer=grid,
                    )
                    # Add a label showing the distance
                    midpoint = (a1_coords + a2_coords) / 2
                    distance = struct.distance(atom1, atom2, units=distance_units)
                    unit = "a₀"

                    if distance_units == DistanceUnits.angstrom:
                        unit = "Å"

                    viewer.addLabel(
                        f"{distance:.2f} {unit}",
                        {
                            "position": {
                                "x": midpoint[0],
                                "y": midpoint[1],
                                "z": midpoint[2],
                            },
                            "backgroundColor": "white",
                            "fontSize": 14,
                            "fontColor": "black",
                        },
                        viewer=grid,
                    )

            if show_indices:
                ang_geom = (
                    struct.geometry_angstrom
                    if not isinstance(struct, list)
                    else struct[0].geometry_angstrom
                )
                for j, coord in enumerate(ang_geom):
                    viewer.addLabel(
                        str(j),
                        {"position": {"x": coord[0], "y": coord[1], "z": coord[2]}},
                        viewer=grid,
                    )

    if not view_2d:
        viewer.setStyle(style or {"stick": {}, "sphere": {"scale": 0.3}})
        viewer.zoomTo()
        html_parts.append(f"{viewer.write_html()}")

    html_parts.append("</div>")
    return "".join(html_parts)


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
            <th>Structure</th>
            <th>Success</th>
            <th>Wall Time</th>
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
            <td>{generate_dictionary_string(
                {
                    "charge": po.input_data.structure.charge, 
                    "multiplicity": po.input_data.structure.multiplicity, 
                    "name": po.input_data.structure.ids.name or "",
                })}</td>
            <td {success_style}>{po.success}</td>
            <td> {
                _format_time(po.provenance.wall_time) if po.provenance.wall_time 
                 else "No timing data"}</td>
            <td>{po.input_data.calctype.name}</td>
            <td>{f"{po.provenance.program} {po.provenance.program_version or ''}"}</td>
            <td>{generate_dictionary_string(po.input_data.model.model_dump(exclude=["extras"]))}</td>
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
        try:
            delta_E = relative_energies[-2]
        except IndexError:
            # If there is only one energy point, set delta_E to nan
            delta_E = np.nan
    else:
        delta_E = relative_energies[-1]

    fig, ax1 = plt.subplots(figsize=figsize)
    color = "tab:blue"
    ax1.set_xlabel("Optimization Cycle")
    ax1.set_ylabel("Relative Energy (kcal/mol)", color=color)
    ax1.plot(relative_energies, label="Energy", marker="o", color="green")
    if last_is_nan:
        ax1.plot(len(relative_energies) - 1, delta_E, marker="x", color="red")
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
        f'Cycle" style="width: 100%; max-width: {DEFAULT_WIDTH}px;">'
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


def _format_time(seconds_float: float) -> str:
    """Format a time in seconds to a human-readable string."""
    hours = int(seconds_float // 3600)
    minutes = int((seconds_float % 3600) // 60)
    seconds = seconds_float % 60
    if hours > 0:
        formatted_time = f"{hours:02}h:{minutes:02}m:{seconds:05.2f}s"
    elif minutes > 0:
        formatted_time = f"{minutes:02}m:{seconds:05.2f}s"
    else:
        formatted_time = f"{seconds:05.2f}s"

    return formatted_time


def generate_results_table(results: Files) -> str:
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
    *structs: Union[Structure, List[Structure]],
    **kwargs,
) -> None:
    """
    Display one or many Structure objects.

    Args:
        *structs: The Structure objects or list of objects to display. If a list is
            passed the structures will be animated.
        **kwargs: Additional keyword arguments to pass to the viewer functions.

    Returns:
        None. Displays the structures in the Jupyter Notebook.
    """
    display(HTML(generate_structure_viewer_html(*structs, **kwargs)))


def program_outputs(
    *prog_outputs: ProgramOutput[Union[ProgramInput, DualProgramInput], Results],
    animate: bool = True,
    struct_viewer: bool = True,
    **kwargs,
) -> None:
    """
    Display one or many ProgramOutput objects.

    Args:
        *prog_outputs: The ProgramOutput objects to display.
        animate: Whether to animate the structure if it is an optimization.
        **kwargs: Additional keyword arguments to pass to the viewer functions.

    Returns:
        None. Displays the ProgramOutput objects in the Jupyter Notebook.
    """

    width = kwargs.get("width", DEFAULT_WIDTH)
    height = kwargs.get("height", DEFAULT_HEIGHT)

    for i, po in enumerate(prog_outputs):
        final_html = []
        final_html.append(generate_output_table(po))

        if isinstance(po.results, ConformerSearchResults):
            structures = [po.input_data.structure] + po.results.conformers
            titles_extra = ["Initial Structure"] + [
                f"Conformer {i}" for i in range(len(po.results.conformers))
            ]
            subtitles = ["Rel Energy: Unknown"] + [
                f"Rel Energy: +{re * constants.HARTREE_TO_KCAL_PER_MOL:.3f} kcal/mol"
                for re in po.results.conformer_energies_relative
            ]
            conf_viewer = generate_structure_viewer_html(
                *structures, titles_extra=titles_extra, subtitles=subtitles, **kwargs
            )
            final_html.append(conf_viewer)
            display(HTML("".join(final_html)))

        else:
            # Create structure viewer
            if not struct_viewer:
                structure_html = "struct_viewer = False"

            else:
                titles_extra = kwargs.pop("titles_extra", [])
                try:
                    title_extra = titles_extra[i]
                except IndexError:
                    title_extra = ""

                # Determine the Structure to use
                if isinstance(po.results, OptimizationResults):
                    for_viewer: Union[Structure, List[Structure]]
                    if animate:
                        for_viewer = po.results.structures
                    else:
                        for_viewer = po.results.final_structure
                        title_extra += " (Final Structure)"

                elif isinstance(po.results, SinglePointResults):
                    for_viewer = po.input_data.structure

                elif isinstance(po.results, Files):
                    for_viewer = po.input_data.structure
                else:
                    raise NotImplementedError(
                        f"Viewing of {type(po.results)} is not yet implemented."
                    )

                structure_html = generate_structure_viewer_html(
                    for_viewer,
                    titles_extra=[title_extra],
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
            <div style="display: flex; align-items: center; justify-content: 
                space-around;">
                <div style="text-align: center; margin-right: 20px; flex: 1;">
                    <div style="display: inline-block; text-align: center;">
                        {structure_html}
                    </div>
                </div>
                <div style="width: {width}px; height: {height}px; text-align: center; 
                    margin-left: 20px; flex: 1; overflow: auto;">
                    {results_html}
                </div>
            </div>
        </div>
                """
            )

            display(HTML("".join(final_html)))


def view(
    *objs: Union[ProgramOutput, Structure, List[Structure]],
    **kwargs,
) -> None:
    """
    Top level method for viewing all qcio objects. This should be the only method you
    need to use to view any qcio object.

    Args:
        *objs: The ProgramOutput or Structure objects to view. May pass one or more
            objects or one or more lists of Structure objects.
        **kwargs: Additional keyword arguments to pass to the viewer functions.

    Returns:
        None. Displays the qcio objects in the Jupyter Notebook.
    """
    if all([isinstance(o, Structure) for o in objs]) or all(
        isinstance(o, Structure) for lst in objs for o in lst
    ):
        structures(*objs, **kwargs)  # type: ignore
        # Handle all structures in a single viewer
        return

    for obj in objs:
        if isinstance(obj, Structure) or isinstance(obj, list):
            structures(*objs, **kwargs)  # type: ignore

        elif isinstance(obj, ProgramOutput):
            program_outputs(obj, **kwargs)

        else:
            raise NotImplementedError(f"Viewing of {type(obj)} is not implemented.")
