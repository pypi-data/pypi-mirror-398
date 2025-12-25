from typing import List
from typing import Sequence


def split_section_size(values: Sequence[float], section_size: int) -> List[slice]:
    """
    This method returns the disjoint slices representing sections of fixed size
    that end higher than start or start higher than end.
    """
    slices = []
    if len(values) == 0:
        return slices

    n = max(len(values), section_size)
    for start in range(0, n, section_size):
        stop = min(start + section_size, len(values))
        if values[start] < values[stop - 1]:
            slices.append(slice(start, stop, 1))
        else:
            start_inv = stop - 1
            stop_inv = start - 1
            if stop_inv == -1:
                stop_inv = None
            slices.append(slice(start_inv, stop_inv, -1))

    return slices
