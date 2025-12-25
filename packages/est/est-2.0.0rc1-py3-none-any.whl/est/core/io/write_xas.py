import logging
from datetime import datetime
from typing import Union

import numpy
from silx.io.dictdump import dicttoh5
from silx.io.dictdump import dicttonx
from silx.io.h5py_utils import File as HDF5File

from ..types.xasobject import XASObject

_logger = logging.getLogger(__name__)


def write_xas(h5_file: str, xas_obj: Union[dict, XASObject]) -> None:
    """
    Save a XASObject in an hdf5 file.
    """
    if isinstance(xas_obj, dict):
        xas_obj = XASObject.from_dict(xas_obj)
    if not isinstance(xas_obj, XASObject):
        raise TypeError(str(type(xas_obj)))

    if not h5_file:
        _logger.warning("no output file defined, please give path to the output file")
        h5_file = input()

    _logger.info("write xas obj to '%s'", h5_file)

    _write_xas(
        h5_file=h5_file,
        energy=xas_obj.energy,
        mu=xas_obj.absorbed_beam(),
        entry=xas_obj.entry,
    )


def _write_xas(
    h5_file,
    entry,
    energy,
    mu,
    start_time=None,
    data_path="/",
    title=None,
    definition=None,
    overwrite=True,
):
    """
    Write raw date in nexus format

    :param str h5_file: path to the hdf5 file
    :param str entry: entry name
    :param sample: definition of the sample
    :type: :class:`.Sample`
    :param energy: beam energy (1D)
    :type: numpy.ndarray
    :param mu: beam absorption (2D)
    :type: numpy.ndarray
    :param start_time:
    :param str data_path:
    :param str title: experiment title
    :param str definition: experiment definition
    """
    h5path = "/".join((data_path, entry))
    nx_dict = {
        "@NX_class": "NXentry",
        "monochromator": {
            "@NX_class": "NXmonochromator",
            "energy": energy,
            "energy@interpretation": "spectrum",
            "energy@NX_class": "NXdata",
            "energy@unit": "eV",
        },
        "absorbed_beam": {
            "@NX_class": "NXdetector",
            "data": mu,
            "data@interpretation": "image",
            "data@NX_class": "NXdata",
        },
        "data": {
            "@NX_class": "NXdata",
            ">energy": "../monochromator/energy",
            ">absorbed_beam": "../absorbed_beam/data",
        },
        "start_time": start_time,
        "title": title,
        "definition": definition,
    }
    if overwrite:
        mode = "w"
        update_mode = "replace"
    else:
        mode = "a"
        update_mode = "add"
    dicttonx(nx_dict, h5_file, h5path=h5path, mode=mode, update_mode=update_mode)


def _write_xas_proc(
    h5_file,
    entry,
    process,
    results,
    processing_order,
    data_path="/",
    overwrite=True,
):
    """
    Write a xas :class:`.Process` into .h5

    :param str h5_file: path to the hdf5 file
    :param str entry: entry name
    :param process: process executed
    :type: :class:`.Process`
    :param results: process result data
    :type: numpy.ndarray
    :param processing_order: processing order of treatment
    :type: int
    :param data_path: path to store the data
    :type: str
    """
    process_name = "xas_process_" + str(processing_order)
    # write the xasproc default information
    with HDF5File(h5_file, "a") as h5f:
        nx_entry = h5f.require_group("/".join((data_path, entry)))
        nx_entry.attrs["NX_class"] = "NXentry"

        nx_process = nx_entry.require_group(process_name)
        nx_process.attrs["NX_class"] = "NXprocess"
        if overwrite:
            for key in (
                "program",
                "version",
                "date",
                "processing_order",
                "class_instance",
                "ft",
            ):
                if key in nx_process:
                    del nx_process[key]
        nx_process["program"] = process.program_name()
        nx_process["version"] = process.program_version()
        nx_process["date"] = datetime.now().replace(microsecond=0).isoformat()
        nx_process["processing_order"] = numpy.int32(processing_order)
        _class = process.__class__
        nx_process["class_instance"] = ".".join((_class.__module__, _class.__name__))

        nx_data = nx_entry.require_group("data")
        nx_data.attrs["NX_class"] = "NXdata"
        nx_data.attrs["signal"] = "data"
        nx_process_path = nx_process.name

    if isinstance(results, numpy.ndarray):
        data_ = {"data": results}
    else:
        data_ = results

    def get_interpretation(my_data):
        """Return hdf5 attribute for this type of data"""
        if isinstance(my_data, numpy.ndarray):
            if my_data.ndim == 1:
                return "spectrum"
            elif my_data.ndim in (2, 3):
                return "image"
        return None

    # save results
    def save_key(key_path, value, attrs):
        """Save the given value to the associated path. Manage numpy arrays
        and dictionaries.
        """
        if attrs is not None:
            assert value is None, "can save value or attribute not both"
        if value is not None:
            assert attrs is None, "can save value or attribute not both"
        key_path = key_path.replace(".", "/")
        # save if is dict
        if isinstance(value, dict):
            h5_path = "/".join((entry, process_name, key_path))
            dicttoh5(
                value,
                h5file=h5_file,
                h5path=h5_path,
                update_mode="replace",
                mode="a",
            )
        else:
            with HDF5File(h5_file, "a") as h5f:
                nx_process = h5f.require_group(nx_process_path)
                if attrs is None:
                    if key_path in nx_process:
                        del nx_process[key_path]
                    try:
                        nx_process[key_path] = value
                    except TypeError as e:
                        _logger.warning(
                            "Unable to write at {} reason is {}"
                            "".format(str(key_path), str(e))
                        )
                    else:
                        interpretation = get_interpretation(value)
                        if interpretation:
                            nx_process[key_path].attrs[
                                "interpretation"
                            ] = interpretation
                else:
                    for key, value in attrs.items():
                        try:
                            nx_process[key_path].attrs[key] = value
                        except Exception as e:
                            _logger.warning(e)

    for key, value in data_.items():
        if isinstance(key, tuple):
            key_path = "/".join(("results", key[0]))
            save_key(key_path=key_path, value=None, attrs={key[1]: value})
        else:
            key_path = "/".join(("results", str(key)))
            save_key(key_path=key_path, value=value, attrs=None)

    if process.getConfiguration() is not None:
        h5_path = "/".join((nx_process_path, "configuration"))
        dicttoh5(
            process.getConfiguration(),
            h5file=h5_file,
            h5path=h5_path,
            update_mode="add",
            mode="a",
        )


if __name__ == "__main__":
    import os

    from ..process.pymca.exafs import PyMca_exafs
    from ..process.pymca.normalization import PyMca_normalization
    from ..types.sample import Sample

    h5_file = "test_xas_123.h5"
    if os.path.exists(h5_file):
        os.remove(h5_file)
    sample = Sample(name="mysample")
    data = numpy.random.rand(256 * 20 * 10)
    data = data.reshape((256, 20, 10))
    process_data = numpy.random.rand(256 * 20 * 10).reshape((256, 20, 10))
    energy = numpy.linspace(start=3.25, stop=3.69, num=256)

    write_xas(h5_file=h5_file, entry="scan1", sample=sample, energy=energy, mu=data)

    process_norm = PyMca_normalization()
    _write_xas_proc(
        h5_file=h5_file,
        entry="scan1",
        process=process_norm,
        results=process_data,
        processing_order=1,
    )
    process_exafs = PyMca_exafs()
    process_data2 = numpy.random.rand(256 * 20 * 10).reshape((256, 20, 10))
    _write_xas_proc(
        h5_file=h5_file,
        entry="scan1",
        process=process_exafs,
        results=process_data2,
        processing_order=2,
    )
