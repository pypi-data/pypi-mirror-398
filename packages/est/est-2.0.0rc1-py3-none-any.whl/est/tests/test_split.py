import numpy
import pytest
from silx.io import dictdump
from silx.utils.retry import RetryTimeoutError

from ..core.process.split import SplitBlissScan
from ..core.split import split_bliss_scan


def split_bliss_scan_task(**kwargs):
    task = SplitBlissScan(inputs=kwargs)
    task.execute()
    return task.outputs.out_urls


@pytest.mark.parametrize("split_function", [split_bliss_scan, split_bliss_scan_task])
@pytest.mark.parametrize(
    "known_subscan_size", [True, False], ids=["known_size", "unknown_size"]
)
def test_split_bliss_scan(tmp_path, split_function, known_subscan_size):
    bliss_scan_data = {
        "1.1": {
            "end_time": "",
            "@attr1": "value1",
            "dataset1": "value1",
            "group1": {
                "@attr2": 10,
                "dataset2": "value2",
                "dataset3": [0, 1, 2, 2, 1, 0],
                "dataset4": [0, 1, 2, 5, 4, 3],
                "dataset5": 10,
                "dataset6": [10, 20],
            },
            "group2": {
                "@attr3": "value3",
                ">dataset3": "../group1/dataset3",
                ">dataset4": "/1.1/group1/dataset4",
            },
        }
    }

    expected_split_data = {
        "1.1": {
            "@attr1": "value1",
            "dataset1": "value1",
            "end_time": "",
            "group1": {
                "@attr2": 10,
                "dataset2": "value2",
                "dataset3": [0, 1, 2],
                "dataset4": [0, 1, 2],
                "dataset5": 10,
            },
            "group2": {
                "@attr3": "value3",
                "dataset3": [0, 1, 2],
                "dataset4": [0, 1, 2],
            },
        },
        "1.2": {
            "@attr1": "value1",
            "dataset1": "value1",
            "end_time": "",
            "group1": {
                "@attr2": 10,
                "dataset2": "value2",
                "dataset3": [0, 1, 2],
                "dataset4": [3, 4, 5],
                "dataset5": 10,
            },
            "group2": {
                "@attr3": "value3",
                "dataset3": [0, 1, 2],
                "dataset4": [3, 4, 5],
            },
        },
    }

    in_file = str(tmp_path / "in.h5")
    dictdump.dicttonx(bliss_scan_data, in_file, add_nx_class=False)

    if known_subscan_size:
        subscan_size = 3
    else:
        subscan_size = None

    out_file = str(tmp_path / "out.h5")
    out_urls = split_function(
        filename=in_file,
        scan_number=1,
        monotonic_channel="group1/dataset3",
        subscan_size=subscan_size,
        out_filename=out_file,
    )

    assert out_urls == [f"silx://{out_file}::/1.1", f"silx://{out_file}::/1.2"]

    split_data = _normalize_h5data(dictdump.nxtodict(out_file, asarray=False))
    assert split_data == expected_split_data


@pytest.mark.parametrize("split_function", [split_bliss_scan, split_bliss_scan_task])
@pytest.mark.parametrize(
    "known_subscan_size", [True, False], ids=["known_size", "unknown_size"]
)
def test_split_unfinished_bliss_scan(tmp_path, split_function, known_subscan_size):
    bliss_scan_data = {
        "1.1": {
            "@attr1": "value1",
            "dataset1": "value1",
            "group1": {
                "@attr2": 10,
                "dataset2": "value2",
                "dataset3": [0, 1, 2, 2, 1, 0],
                "dataset4": [0, 1, 2, 5, 4, 3],
                "dataset5": 10,
                "dataset6": [10, 20],
            },
            "group2": {
                "@attr3": "value3",
                ">dataset3": "../group1/dataset3",
                ">dataset4": "/1.1/group1/dataset4",
            },
        }
    }

    expected_split_data = {
        "1.1": {
            "@attr1": "value1",
            "dataset1": "value1",
            "group1": {
                "@attr2": 10,
                "dataset2": "value2",
                "dataset3": [0, 1, 2],
                "dataset4": [0, 1, 2],
                "dataset5": 10,
            },
            "group2": {
                "@attr3": "value3",
                "dataset3": [0, 1, 2],
                "dataset4": [0, 1, 2],
            },
        }
    }

    in_file = str(tmp_path / "in.h5")
    dictdump.dicttonx(bliss_scan_data, in_file, add_nx_class=False)

    if known_subscan_size:
        subscan_size = 3
    else:
        subscan_size = None

    out_file = str(tmp_path / "out.h5")
    out_urls = split_function(
        filename=in_file,
        scan_number=1,
        monotonic_channel="group1/dataset3",
        subscan_size=subscan_size,
        out_filename=out_file,
        wait_finished=False,
        counter_group="group2",
    )

    assert out_urls == [f"silx://{out_file}::/1.1"]

    split_data = _normalize_h5data(dictdump.nxtodict(out_file, asarray=False))
    assert split_data == expected_split_data


@pytest.mark.parametrize("split_function", [split_bliss_scan, split_bliss_scan_task])
@pytest.mark.parametrize(
    "known_subscan_size", [True, False], ids=["known_size", "unknown_size"]
)
def test_split_bliss_scan_timeout(tmp_path, split_function, known_subscan_size):
    bliss_scan_data = {
        "1.1": {
            "@attr1": "value1",
            "dataset1": "value1",
            "group1": {
                "@attr2": 10,
                "dataset2": "value2",
                "dataset3": [0, 1, 2, 2, 1, 0],
                "dataset4": [0, 1, 2, 5, 4, 3],
                "dataset5": 10,
                "dataset6": [10, 20],
            },
            "group2": {
                "@attr3": "value3",
                ">dataset3": "../group1/dataset3",
                ">dataset4": "/1.1/group1/dataset4",
            },
        }
    }

    in_file = str(tmp_path / "in.h5")
    dictdump.dicttonx(bliss_scan_data, in_file, add_nx_class=False)

    if known_subscan_size:
        subscan_size = 3
    else:
        subscan_size = None

    out_file = tmp_path / "out.h5"

    if split_function is split_bliss_scan_task:
        exc = RuntimeError
    else:
        exc = RetryTimeoutError

    with pytest.raises(exc):
        _ = split_function(
            filename=in_file,
            scan_number=1,
            monotonic_channel="group1/dataset3",
            subscan_size=subscan_size,
            out_filename=out_file,
            retry_timeout=0.1,
        )

    assert not out_file.exists()


def _normalize_h5data(data):
    if isinstance(data, dict):
        return {k: _normalize_h5data(v) for k, v in data.items()}
    if isinstance(data, bytes):
        return data.decode()
    if isinstance(data, numpy.ndarray):
        return data.tolist()
    return data
