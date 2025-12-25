from typing import Union

import numpy
import pint
import silx.io.h5py_utils
from pint.errors import UndefinedUnitError
from silx.io.url import DataUrl

from ....units import ur


def get_dataset(url: DataUrl) -> Union[numpy.ndarray, pint.Quantity]:
    data_path = url.data_path()
    data_slice = url.data_slice()

    with silx.io.h5py_utils.File(url.file_path(), "r") as h5:
        dset = h5[data_path]

        units = dset.attrs.get("units")

        if not silx.io.is_dataset(dset):
            raise ValueError("Data path from URL '%s' is not a dataset" % url.path())

        if data_slice is not None:
            data = silx.io.utils.h5py_read_dataset(dset, index=data_slice)
        else:
            data = silx.io.utils.h5py_read_dataset(dset)

        if units:
            try:
                units = ur(units)
            except UndefinedUnitError:
                units = None

        if units:
            return data * units
        return data
