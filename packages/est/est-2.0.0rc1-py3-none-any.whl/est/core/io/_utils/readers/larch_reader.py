import functools
from typing import Dict
from typing import List

import numpy

try:
    from larch.io import columnfile
except ImportError:
    columnfile = None


def get_first_scan_title(file_path: str) -> None:
    return None


def get_all_scan_titles(file_path: str) -> List[str]:
    return list()


def get_scan_column_names(file_path: str, scan_title: str) -> List[str]:
    return list(_read_columnfile(file_path))


def read_scan_column(file_path, col_name: str, scan_title: str) -> numpy.ndarray:
    table = _read_columnfile(file_path)
    if col_name not in table:
        return numpy.array([])
    return table[col_name]


@functools.lru_cache(maxsize=1)
def _read_columnfile(column_file: str) -> Dict[str, numpy.ndarray]:
    if columnfile is None:
        raise ImportError("Larch not imported")
    larch_group = columnfile.read_ascii(column_file)
    return dict(zip(larch_group.array_labels, larch_group.data))
