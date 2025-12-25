import logging
import os
from contextlib import contextmanager
from typing import Generator
from typing import List
from typing import Optional

import h5py
import numpy
from silx.io import h5py_utils
from silx.utils.retry import RetryError

from .monotonic import split_piecewise_monotonic
from .sections import split_section_size

_logger = logging.getLogger(__name__)


def split_bliss_scan(
    filename: str,
    scan_number: int,
    monotonic_channel: str,
    out_filename: str,
    subscan_size: Optional[int] = None,
    trim_n_points: Optional[int] = None,
    wait_finished: bool = True,
    counter_group: Optional[str] = None,
    **retry_args,
) -> List[str]:
    """Split a Bliss scan in subscans as determined by a channel which
    is monotonically increasing or descreasing in each subscan or determined
    by subscan size.

    :param filename: HDF5 file name containing the Bliss scan.
    :param scan_number: The Bliss scan number.
    :param monotonic_channel: HDF5 path relative to the scan group.
    :param out_filename: HDF5 file name to save subscans as a result of splitting the Bliss scan.
    :param subscan_size: Fix length subscan size.
    :param trim_n_points: Trim N points from the start and end of each subscan.
    :param wait_finished: Wait for the Bliss scan to be complete in HDF5.
    :param counter_group: Group with counters to determine the number of scan points.
    :param retry_timeout: Timeout of waiting for the Bliss scan to be complete in HDF5.
    :param retry_period: Check period of waiting for the Bliss scan to be complete in HDF5.
    :returns: HDF5 URL's of the subscans as a result of splitting the Bliss scan.
    """
    if subscan_size is None:
        subscan_size = 0
    else:
        assert subscan_size >= 0

    if trim_n_points is None:
        trim_n_points = 0
    else:
        assert trim_n_points >= 0

    entry_name = f"{scan_number}.1"

    out_urls = []
    with _open_scan_entry(
        filename,
        entry_name,
        monotonic_channel,
        counter_group,
        wait_finished=wait_finished,
        **retry_args,
    ) as nxentry_in:

        if nxentry_in is None:
            return []

        if wait_finished:
            finished = True
        else:
            finished = "end_time" in nxentry_in

        if finished:
            npoints = None
        else:
            npoints = _number_of_scan_points(nxentry_in, counter_group)

        if npoints is None:
            monotonic_values = nxentry_in[monotonic_channel][()]
        else:
            monotonic_values = nxentry_in[monotonic_channel][:npoints]

        if subscan_size:
            subscan_slices = split_section_size(monotonic_values, subscan_size)
        else:
            subscan_slices = split_piecewise_monotonic(monotonic_values)

        if not finished:
            subscan_slices = subscan_slices[:-1]
            subscan_slices = _select_complete_subscans(
                nxentry_in, subscan_slices, counter_group
            )

        for subscan_number, subscan_slice in enumerate(subscan_slices, 1):
            out_url = _save_subscan(
                nxentry_in,
                scan_number,
                subscan_number,
                out_filename,
                subscan_slice,
                trim_n_points,
                **retry_args,
            )
            out_urls.append(out_url)
    return out_urls


def _number_of_scan_points(
    nxentry_in: h5py.Group, counter_group: Optional[str]
) -> Optional[int]:
    if counter_group and counter_group in nxentry_in:
        counters = nxentry_in[counter_group]
        sizes = [counters[name].size for name in counters]
        if sizes:
            return min(sizes)


def _select_complete_subscans(
    nxentry_in: h5py.Group, subscan_slices: List[slice], counter_group: Optional[str]
) -> List[slice]:
    complete_subscan_slices = []
    for subscan_slice in subscan_slices:
        if not _subscan_is_complete(nxentry_in, subscan_slice, counter_group):
            break
        complete_subscan_slices.append(subscan_slice)
    return complete_subscan_slices


def _subscan_is_complete(
    nxentry_in: h5py.Group, subscan_slice: slice, counter_group: Optional[str]
) -> bool:
    if not counter_group:
        return True
    if counter_group not in nxentry_in:
        return False
    if subscan_slice.step and subscan_slice.step < 0:
        nexpected = subscan_slice.start
    else:
        nexpected = subscan_slice.stop
    counters = nxentry_in[counter_group]
    sizes = [counters[name].size >= nexpected for name in counters]
    if sizes:
        return all(sizes)
    return False


@contextmanager
def _open_scan_entry(
    filename: str,
    entry_name: str,
    *paths: Optional[str],
    wait_finished: bool = False,
    **retry_args,
) -> Generator[Optional[h5py.Group], None, None]:
    if not wait_finished:
        _ = retry_args.setdefault("retry_timeout", 10)
    try:
        with _open_scan_retry(
            filename, entry_name, *paths, wait_finished=wait_finished, **retry_args
        ) as nxentry_in:
            yield nxentry_in
    except Exception as ex:
        if wait_finished:
            raise
        _logger.warning("%s::%s not complete (%s)", filename, entry_name, ex)
        yield None


@h5py_utils.retry_contextmanager()
def _open_scan_retry(
    filename: str,
    entry_name: str,
    *paths: Optional[str],
    wait_finished: bool = False,
) -> Generator[Optional[h5py.Group], None, None]:
    with h5py_utils.File(filename) as nxroot_in:
        try:
            nxentry_in = nxroot_in[entry_name]
            if wait_finished:
                _ = nxentry_in["end_time"]
            for path in paths:
                if path is not None:
                    _ = nxentry_in[path]
        except Exception:
            raise RetryError

        yield nxentry_in


def _save_subscan(
    nxentry_in: h5py.Group,
    scan_number: int,
    subscan_number: int,
    out_filename: str,
    subscan_slice: slice,
    trim_n_points: int,
    **retry_args,
) -> str:
    entry_name = f"{scan_number}.{subscan_number}"
    out_url = f"silx://{out_filename}::/{entry_name}"

    dirname = os.path.dirname(out_filename)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    _ = retry_args.setdefault("retry_timeout", 60)

    with h5py_utils.open_item(
        out_filename, "/", mode="a", track_order=True, **retry_args
    ) as nxroot_out:
        if entry_name in nxroot_out:
            _logger.warning("%s::/%s already exists", out_filename, entry_name)
            return out_url
        nxentry_out = nxroot_out.create_group(entry_name)
        _save_subgroup(nxentry_in, nxentry_out, subscan_slice, trim_n_points)
    return out_url


def _save_subgroup(
    group_in: h5py.Group, group_out: h5py.Group, dim0_slice: slice, trim_n_points: int
) -> None:
    group_out.attrs.update(group_in.attrs)

    for name in group_in:

        link = group_in.get(name, getlink=True)
        if isinstance(link, h5py.SoftLink):
            target = _relative_link(group_in, link.path, group_out)
            group_out[name] = h5py.SoftLink(path=target)
            continue

        h5item = group_in[name]
        if isinstance(h5item, h5py.Group):
            _save_subgroup(
                h5item, group_out.create_group(name), dim0_slice, trim_n_points
            )
            continue

        if isinstance(h5item, h5py.Dataset):
            if h5item.size > 1:
                try:
                    data = _slice_dataset(h5item, dim0_slice)
                except Exception:
                    _logger.warning(
                        "%s with shape %s cannot be sliced by %s",
                        h5item.name,
                        h5item.shape,
                        dim0_slice,
                    )
                    continue
                if trim_n_points:
                    data = data[trim_n_points:-trim_n_points]
            else:
                data = h5item[()]
            dset_out = group_out.create_dataset(name, data=data)
            dset_out.attrs.update(h5item.attrs)
            continue

        _logger.warning("%s of type %s is not supported", h5item.name, type(h5item))


def _relative_link(
    org_parent: h5py.Group, link_target: str, new_parent: h5py.Group
) -> str:

    parent_path = org_parent.name.replace("/", os.path.sep)
    link_target_path = link_target.replace("/", os.path.sep)
    rel_link_target_path = os.path.relpath(link_target_path, parent_path)
    new_link_target_path = os.path.join(new_parent.name, rel_link_target_path)
    return os.path.normpath(new_link_target_path)


def _slice_dataset(h5dataset: h5py.Dataset, dim0_slice: slice) -> numpy.ndarray:
    expected_size = (dim0_slice.stop - dim0_slice.start) // dim0_slice.step

    if dim0_slice.step and dim0_slice.step < 0:
        start = dim0_slice.stop + 1
        stop = dim0_slice.start + 1
        step = -dim0_slice.step
        data = h5dataset[start:stop:step]
        if len(data) != expected_size:
            raise ValueError("slice does not have the expected size")
        return data[::-1]
    else:
        data = h5dataset[dim0_slice]
        if len(data) != expected_size:
            raise ValueError("slice does not have the expected size")
        return data
