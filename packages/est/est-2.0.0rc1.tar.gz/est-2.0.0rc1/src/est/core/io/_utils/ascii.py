import os
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union

import numpy
from silx.io.url import DataUrl

from .readers import ascii_reader
from .readers import larch_reader
from .readers import spec_reader


def read_column(
    data_url: Union[DataUrl, str],
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    data_info = split_ascii_url(data_url)
    reader = _get_reader(data_info.file_path, scheme=data_info.scheme)
    return reader.read_scan_column(
        data_info.file_path, data_info.col_name, data_info.scan_title
    )


def get_first_scan_title(file_path: str) -> Optional[str]:
    reader = _get_reader(file_path)
    return reader.get_first_scan_title(file_path)


def get_all_scan_titles(file_path: str) -> List[str]:
    reader = _get_reader(file_path)
    return reader.get_all_scan_titles(file_path)


def get_scan_column_names(file_path: str, scan_title: str) -> List[str]:
    reader = _get_reader(file_path)
    return reader.get_scan_column_names(file_path, scan_title)


SliceLike = Union[slice, int, type(Ellipsis)]


class AsciiColumn(NamedTuple):
    scheme: str
    file_path: str
    scan_title: Optional[str]
    col_name: Optional[str]
    data_slice: Optional[Tuple[SliceLike, ...]]


def split_ascii_url(data_url: Union[str, DataUrl]) -> AsciiColumn:
    """
    URL examples:

    - ascii:///tmp/data/EXAFS_Ge1.csv?/mu
    - spec:///tmp/data/EXAFS_Ge1.dat?/1.1/mu
    """
    if isinstance(data_url, str):
        data_url = DataUrl(path=data_url)
    if not isinstance(data_url, DataUrl):
        raise TypeError(f"data_url must of a DataUrl, not {type(data_url)}")

    # Split data path in scan title and column name
    scan_title = None
    col_name = None
    data_path = data_url.data_path()
    if data_path:
        parts = data_path.split("/")
        if len(parts) == 1:
            scan_title = None
            col_name = parts[0]
        else:
            scan_title = parts[0]
            col_name = "/".join(parts[1:])

    return AsciiColumn(
        scheme=data_url.scheme(),
        file_path=data_url.file_path(),
        scan_title=scan_title,
        col_name=col_name,
        data_slice=data_url.data_slice(),
    )


def build_ascii_data_url(
    file_path: str,
    col_name: str,
    scan_title: Optional[str] = None,
    data_slice: Optional[Tuple[SliceLike, ...]] = None,
):
    if scan_title is None:
        scan_title = get_first_scan_title(file_path)
    if scan_title is None:
        scan_title = ""

    if "/" in scan_title:
        raise ValueError("scan_title cannot contain '/'")
    data_path = f"{scan_title}/{col_name}"

    _, ext = os.path.splitext(file_path)
    if ext == ".xmu":
        scheme = "larch"
    elif ext == ".spec" or _is_spec(file_path):
        scheme = "spec"
    else:
        scheme = "ascii"

    return DataUrl(
        file_path=file_path,
        data_path=data_path,
        data_slice=data_slice,
        scheme=scheme,
    )


def _get_reader(file_path: str, scheme: Optional[str] = None):
    _, ext = os.path.splitext(file_path)
    if scheme == "larch" or ext == ".xmu":
        return larch_reader
    if scheme == "spec" or ext == ".spec" or _is_spec(file_path):
        return spec_reader
    return ascii_reader


def _is_spec(file_path: str) -> bool:
    if not os.path.isfile(file_path):
        return False

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                return line.startswith("#F ")

    return False
