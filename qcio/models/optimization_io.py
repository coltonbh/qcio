"""Creating a few quick optimization models for testing purposes."""
from typing import List

from .base_io import ComputedPropsBase, ProgramInputBase, ResultBase
from .single_point_io import SinglePointArgs, SinglePointResult


class OptimizationInput(ProgramInputBase):
    """Input model for an optimization."""

    sp_args: SinglePointArgs
    sp_program: str


class OptimizationComputedProps(ComputedPropsBase):
    """Computed properties for an optimization."""

    energies: List[float]
    trajectory: List[SinglePointResult] = []


class OptimizationResult(ResultBase):
    input_data: OptimizationInput
    computed: OptimizationComputedProps
