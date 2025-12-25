from silx.io.url import DataUrl

from ..core.io._utils.ascii import split_ascii_url
from ..core.io.read_xas import build_ascii_data_url


def test_spec_url():
    """simple test of the spec url function class"""
    file_path = "test.dat"
    scan_title = "1.1"
    col_name = "energy"
    data_slice = None
    url = build_ascii_data_url(
        file_path=file_path,
        scan_title=scan_title,
        col_name=col_name,
        data_slice=data_slice,
    )
    assert isinstance(url, DataUrl)
    expected = ("ascii", file_path, scan_title, col_name, data_slice)
    assert split_ascii_url(url) == expected
