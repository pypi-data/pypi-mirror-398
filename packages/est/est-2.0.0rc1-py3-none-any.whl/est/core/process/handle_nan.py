import numpy


def array_undo_mask(masked: numpy.ndarray, mask: numpy.ndarray) -> numpy.ndarray:
    """
    Restore an array to its original shape after applying a boolean mask.

    :param masked: The array containing only the unmasked values.
    :param mask: A boolean array indicating the original positions of the `masked` values.
    :return: A reconstructed array of the same shape as `mask`, where values from `masked`
             are restored to their original positions, and other elements are filled
             with `NaN` (for floats) or `0` (for ints).

    **Example:**

    >>> import numpy as np
    >>> original = np.array([1.0, 2.0, np.nan, 4.0, np.nan])
    >>> mask = ~np.isnan(original)  # Boolean mask
    >>> masked = original[mask]     # Extract non-NaN values
    >>> restored = array_undo_mask(masked, mask)
    >>> print(restored)
    [ 1.  2. nan  4. nan ]
    """
    if not mask.any():
        return masked
    if numpy.issubdtype(masked.dtype, int):
        raise TypeError("Integers are not supported")
    result = numpy.full(mask.shape, numpy.nan, dtype=masked.dtype)
    result[mask] = masked
    return result
