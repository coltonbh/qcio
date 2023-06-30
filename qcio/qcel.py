"""Compatibility layer for QCElemental (QCSchema)."""
from typing import Any, Dict, Union

from qcio import (
    ProgramFailure,
    ProgramInput,
    Provenance,
    SinglePointOutput,
    SinglePointResults,
    Wavefunction,
)


def to_qcel_input(inp_obj: ProgramInput) -> Dict[str, Any]:
    """Return the QCElemental v1 input schema representation of the input
    (AtomicInput dict).

    Returns:
        The QCElemental v1 dict representation of an AtomicInput object.
    """
    return {
        "molecule": {
            "symbols": inp_obj.molecule.symbols,
            "geometry": inp_obj.molecule.geometry,
            "molecular_charge": inp_obj.molecule.charge,
            "molecular_multiplicity": inp_obj.molecule.multiplicity,
            "identifiers": {
                key: value
                for key, value in inp_obj.molecule.identifiers.dict().items()
                if key not in ["name_IUPAC", "name_common"]  # not on qcel model
            },
        },
        "driver": inp_obj.calctype,
        "model": inp_obj.model.dict(),
        "keywords": inp_obj.keywords,
        "extras": inp_obj.extras,
    }


def from_qcel_output(
    qcio_input: ProgramInput,
    qcel_output: Dict[str, Any],
) -> Union[SinglePointOutput, ProgramFailure]:
    """Create a SinglePointSuccessfulOutput or SinglePointFailedOutput from the
    QCElemental v1 output schema representation of the output (AtomicResult dict).

    NOTE: Function no longer used in qcop; only using from_qcel_output_results. Maybe
        remove in the future if I never return to use it.

    Args:
        qcio_input: The input object for the computation.
        qcel_output: The QCElemental v1 output schema representation of the output.
            May be a dict representing an AtomicResult or FailedOperation.
    """
    prov_extras = {"NOTE": "Computed by QCEngine"}

    if qcel_output["success"] is False:
        return ProgramFailure(
            input_data=qcio_input,
            traceback=qcel_output["error"]["error_message"],
            provenance=Provenance(
                program=qcel_output["input_data"]["provenance"]["creator"],
                program_version=qcel_output["input_data"]["provenance"].get("version"),
                wall_time=qcel_output["input_data"]["provenance"].get("wall_time"),
                extras=prov_extras,
            ),
            extras=qcel_output["extras"] or {},  # Because .extras may be None
        )
    else:
        return SinglePointOutput(
            input_data=qcio_input,
            stdout=qcel_output["stdout"],
            results=from_qcel_output_results(qcel_output),
            provenance=Provenance(
                program=qcel_output["provenance"]["creator"],
                program_version=qcel_output["provenance"].get("version"),
                wall_time=qcel_output["provenance"].get("wall_time"),
                extras=prov_extras,
            ),
        )


def from_qcel_output_results(
    qcel_output: Dict[str, Any],
) -> SinglePointResults:
    """Create a SinglePointSuccessfulOutput or SinglePointFailedOutput from the
    QCElemental v1 output schema representation of the output (AtomicResult dict).

    Args:
        qcel_output: The QCElemental v1 output schema representation of the output.
            May be a dict representing an AtomicResult or FailedOperation.
    """
    # Collect values from keys that exist in qcio
    qcio_to_qcel = {
        "calcinfo_natoms": "calcinfo_natom",
        "energy": "return_energy",
        "gradient": "return_gradient",
        "hessian": "return_hessian",
    }
    results = {}
    for key in SinglePointResults.__annotations__:
        if key in qcio_to_qcel:
            qcel_key = qcio_to_qcel[key]
        else:
            qcel_key = key
        value = qcel_output["properties"].get(qcel_key)
        if value is not None:
            results[key] = value

    if qcel_output["wavefunction"]:
        results["wavefunction"] = {
            key: value
            for key, value in qcel_output["wavefunction"].items()
            if key in Wavefunction.__annotations__
        }

    results["extras"] = {"extras": {"NOTE": "Results computed using QCEngine"}}
    return SinglePointResults(**results)