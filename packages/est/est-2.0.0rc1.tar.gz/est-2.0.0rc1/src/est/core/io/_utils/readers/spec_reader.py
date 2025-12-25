import functools
import os
from contextlib import contextmanager
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional

import numpy
from silx.io.specfile import SfErrFileOpen
from silx.io.spech5 import SpecFile


def get_first_scan_title(file_path: str) -> Optional[str]:
    with _handle_spec_errors(file_path):
        spec_file = SpecFile(file_path)
        try:
            scan = spec_file[0]
        except IndexError:
            return None
        return scan.scan_header_dict["S"]


def get_all_scan_titles(file_path: str) -> List[str]:
    with _handle_spec_errors(file_path):
        return [scan.scan_header_dict["S"] for scan in SpecFile(file_path)]


def get_scan_column_names(file_path: str, scan_title: str) -> List[str]:
    with _handle_spec_errors(file_path):
        for scan in SpecFile(file_path):
            if not scan_title or scan_title == scan.scan_header_dict["S"]:
                return scan.labels
        return list()


def read_scan_column(file_path: str, col_name: str, scan_title: str) -> numpy.ndarray:
    table = _read_scan(file_path, scan_title)
    if col_name not in table:
        return numpy.array([])
    return table[col_name]


@functools.lru_cache(maxsize=1)
def _read_scan(file_path: str, scan_title: str) -> Dict[str, numpy.ndarray]:
    try:
        with _handle_spec_errors(file_path):
            spec_file = SpecFile(file_path)
    except SfErrFileOpen:
        if _is_empty(file_path):
            return dict()
        raise

    for scan in spec_file:
        is_scan = scan_title == scan.scan_header_dict["S"]
        if not is_scan:
            if scan_title is None:
                continue
            return dict()

        return dict(zip(scan.labels, scan.data))

    return dict()


def _is_empty(file_path: str) -> bool:
    with open(file_path, "r") as f:
        for line in f:
            if line:
                return False
    return True


@contextmanager
def _handle_spec_errors(file_path: str) -> Generator[None, None, None]:
    try:
        yield
    except SfErrFileOpen as e:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No such file or directory: {file_path!r}") from e
        raise
