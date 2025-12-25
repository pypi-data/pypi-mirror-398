from typing import Optional
from typing import Sequence

import numpy
from numpy.typing import ArrayLike

DimensionsType = Sequence[int]
# Dimensions of X, Y and Energy.

STANDARD_DIMENSIONS: DimensionsType = (2, 1, 0)
# The standard dataset axes are (Energy, Y, X).


def transform_to_standard(
    data: ArrayLike, dimensions: Optional[DimensionsType]
) -> ArrayLike:
    if data.ndim > 3:
        raise ValueError("Cannot handle numpy arrays with a rank higher than 1")

    if data.ndim == 1:
        # Single spectrum
        data = data[..., numpy.newaxis]

    if data.ndim == 2:
        # List of Spectra
        data = data[..., numpy.newaxis]

    dimensions = parse_dimensions(dimensions)
    dst_axis = (
        dimensions.index(STANDARD_DIMENSIONS[0]),
        dimensions.index(STANDARD_DIMENSIONS[1]),
        dimensions.index(STANDARD_DIMENSIONS[2]),
    )

    src_axis = (0, 1, 2)
    if src_axis == dst_axis:
        return data
    return numpy.moveaxis(data, src_axis, dst_axis)


def parse_dimensions(dimensions: Optional[DimensionsType]) -> DimensionsType:
    if dimensions is None:
        return STANDARD_DIMENSIONS
    _validate_dimensions_type(dimensions)
    return dimensions


def _validate_dimensions_type(dimensions: DimensionsType) -> None:
    if len(dimensions) != 3:
        raise TypeError("Dimensions should have three integers")
    if set(dimensions) != {0, 1, 2}:
        raise TypeError("Dimensions should have three values: 0, 1 and 2")
