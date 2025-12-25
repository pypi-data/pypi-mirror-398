import functools
import warnings
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import numpy


def get_first_scan_title(file_path: str) -> None:
    return None


def get_all_scan_titles(file_path: str) -> List[str]:
    return list()


def get_scan_column_names(file_path: str, scan_title: str) -> List[str]:
    columns, _, _ = _ascii_header(file_path)
    return columns


def read_scan_column(file_path, col_name: str, scan_title: str) -> numpy.ndarray:
    columns, delimiter, skiprows = _ascii_header(file_path)
    if not columns:
        return numpy.array([])
    table = _read_data(file_path, tuple(columns), delimiter, skiprows)
    if col_name not in table:
        return numpy.array([])
    return table[col_name]


@functools.lru_cache(maxsize=1)
def _ascii_header(ascii_file: str) -> Tuple[List[str], Optional[str], int]:
    firstline = ""
    skiprows = 0

    with open(ascii_file, "r") as csvfile:
        for rawline in csvfile:
            line = rawline.strip()
            skiprows += 1
            if line and not line.startswith("#"):
                firstline = line
                break

    if not firstline:
        return [], "", skiprows

    delimiter = ","
    for cand in [",", ";", " "]:
        columns = firstline.split(cand)
        if len(columns) > 1:
            delimiter = cand
            break

    if delimiter == " ":
        delimiter = None

    # First line is a header
    try:
        _ = float(columns[0])
    except ValueError:
        columns = [s.strip() for s in columns]
        return columns, delimiter, skiprows

    # First line is data
    skiprows -= 1
    columns = [f"Column {i+1}" for i in range(len(columns))]
    return columns, delimiter, skiprows


@functools.lru_cache(maxsize=1)
def _read_data(
    ascii_file: str, columns: Tuple[str], delimiter: Optional[str], skiprows: int
) -> Dict[str, numpy.ndarray]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*no data.*", category=UserWarning)
        data = numpy.loadtxt(ascii_file, delimiter=delimiter, skiprows=skiprows)
        return dict(zip(columns, data.T))
