from typing import List
from typing import Sequence
from typing import Tuple

import numpy


def split_piecewise_monotonic(values: Sequence[float]) -> List[slice]:
    """This method returns the disjoint slices representing monotonic sections.

    The provided values are assumed to be piecewise monotonic which means that
    it consists of sections that are either monotonically increasing (∀ i ≤ j, x[i] ≤ x[j])
    or monotonically decreasing (∀ i ≤ j, x[i] ≥ x[j]). Note that a list of identical
    values is both monotonically increasing and decreasing.
    """
    section_sizes = []
    section_slopes = []
    values_left = values
    while len(values_left):
        section_size, section_slope = _first_monotonic_size(values_left)
        section_sizes.append(section_size)
        section_slopes.append(section_slope)
        values_left = values_left[section_size:]

    monotone_start = [0]
    monotone_stop = []
    monotone_step = []
    last_section_index = len(section_sizes) - 1
    stops = numpy.cumsum(section_sizes)
    for section_index, (stop, section_slope) in enumerate(zip(stops, section_slopes)):
        monotone_step.append(1 if section_slope >= 0 else -1)

        if section_index == last_section_index:
            monotone_stop.append(stop)
            break

        # The pivot index is the index at which either
        #  - slope>=0 with the previous index and slope<0 with the next index
        #  - slope<=0 with the previous index and slope>0 with the next index
        pivot_index = stop - 1

        if values[pivot_index - 1] == values[pivot_index]:
            # The pivot index ■ is part of the next section
            #
            #    ● ─ ■
            #   /     \     -> same slope up and down
            #  ●       ●
            #
            monotone_stop.append(stop - 1)
            monotone_start.append(stop - 1)
            continue

        # Determine whether the pivot index is part of this section or
        # be part of the next section
        slope_before = values[pivot_index] - values[pivot_index - 1]
        diff_slope_before = abs(section_slope - slope_before)

        slope_after = values[pivot_index + 1] - values[pivot_index]
        next_section_slope = section_slopes[section_index + 1]
        diff_slope_after = abs(next_section_slope - slope_after)

        if diff_slope_after <= diff_slope_before:
            # The pivot index ■ is part of the next section
            #
            #       ■
            #    ●   \       -> slope after matches the next section slope better
            #   /     ●         then the slope before matches the current section slope
            #  ●       \
            # /         ●
            #
            monotone_stop.append(stop - 1)
            monotone_start.append(stop - 1)
        else:
            # The pivot index ■ is part of this section
            #
            #     ■
            #    /   ●      -> slope before matches the current section slope better
            #   ●     \        than the slope after matches the next section slope
            #  /       ●
            # ●         \
            #
            monotone_stop.append(stop)
            monotone_start.append(stop)

    return [
        _create_slice(start, stop, step)
        for start, stop, step in zip(monotone_start, monotone_stop, monotone_step)
    ]


def _create_slice(start: int, stop: int, step: int):
    if step >= 0:
        return slice(start, stop, step)
    assert start >= 0
    assert stop >= 0
    start, stop = stop, start
    start -= 1
    if stop == 0:
        stop = None
    else:
        stop -= 1
    return slice(start, stop, step)


def _mean_nonzero(values: Sequence[float]) -> float:
    """Average non-zero value. Returns `nan` for an empty list and `0.` when
    all values are zero.
    """
    values = numpy.asarray(values)
    if not values.size:
        return numpy.nan
    non_zero = values != 0
    if non_zero.any():
        return numpy.mean(values[non_zero])
    return 0.0


def _first_monotonic_size(values: Sequence[float]) -> Tuple[int, int]:
    """Determine the length of the first monotonically increasing or decreasing slice
    starting from the first value.
    """
    slopes = numpy.diff(values)

    maxsize = len(values)
    if maxsize < 3:
        return maxsize, _mean_nonzero(slopes)

    slope_signs = numpy.sign(slopes)
    first_slope_sign = slope_signs[0]
    for value_idx, slope_sign in enumerate(slope_signs[1:], 1):
        if slope_sign and first_slope_sign and slope_sign != first_slope_sign:
            # Non-zero slope changed sign: end of monotonic series
            return value_idx + 1, _mean_nonzero(slopes[:value_idx])
        if not first_slope_sign:
            first_slope_sign = slope_sign

    return maxsize, _mean_nonzero(slopes)
