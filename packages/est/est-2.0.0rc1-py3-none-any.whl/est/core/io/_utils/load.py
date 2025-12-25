import logging
import os
from typing import Optional
from typing import Union

import numpy
import pint
import silx.io.h5py_utils
import silx.io.utils
from silx.io.url import DataUrl
from silx.utils.retry import RetryError

from .... import settings
from ...types.data import InputType
from .ascii import read_column
from .readers import fabio_reader
from .readers import silx_reader

try:
    is_h5py_exception = silx.io.h5py_utils.is_h5py_exception
except AttributeError:
    is_h5py_exception = silx.io.h5py_utils._is_h5py_exception


_logger = logging.getLogger(__name__)


def _retry_on_error(e):
    if is_h5py_exception(e):
        return isinstance(e, (OSError, RuntimeError, KeyError))
    return isinstance(e, RetryError)


@silx.io.h5py_utils.retry(
    retry_timeout=settings.DEFAULT_READ_TIMEOUT, retry_on_error=_retry_on_error
)
def load_data(
    data_url: Union[DataUrl, str, None],
) -> Union[numpy.ndarray, pint.Quantity, None]:
    """
    Load a specific dataset from a url. Accepts URL schemes silx, fabio, numpy, PyMca and xraylarch.

    - HDF5 URL: read HDF5 dataset
    - ASCII URL: read ASCII column
    - EDF, TIFF, ...: read all data

    Some examples of URL's

    - silx:///users/foo/image.edf::/scan_0/instrument/detector_0/data[0]
    - fabio:///users/foo/image.edf::[0]
    - ascii:///tmp/data/EXAFS_Ge1.csv?/mu
    """
    if data_url is None:
        return None
    data_url = _get_url_with_scheme(data_url)

    scheme = data_url.scheme().lower()

    if scheme in _ASCII_SCHEMES:
        return read_column(data_url)

    if scheme == "numpy":
        return numpy.load(data_url.file_path())

    if scheme == "silx":
        return silx_reader.get_dataset(data_url)

    if scheme == "fabio":
        return fabio_reader.get_dataset(data_url)

    if not data_url.is_valid():
        _logger.warning("invalid url: %s", data_url)
        return None

    _logger.error("Scheme '%s' not supported", data_url.scheme())
    return None


def get_input_type(data_url: Union[DataUrl, str, None]) -> Optional[InputType]:
    if data_url is None:
        return InputType.ascii_spectrum

    data_url = _get_url_with_scheme(data_url)
    if data_url.scheme().lower() in _ASCII_SCHEMES:
        return InputType.ascii_spectrum
    else:
        return InputType.hdf5_spectra


def _get_url_with_scheme(data_url: Union[DataUrl, str]) -> DataUrl:
    if not isinstance(data_url, (str, DataUrl)):
        raise TypeError(f"Url must of type 'str' or 'DataUrl', not {type(data_url)!r}")

    if isinstance(data_url, str):
        data_url = DataUrl(path=data_url)
    if data_url.scheme():
        return data_url

    params = dict(
        file_path=data_url.file_path(),
        data_path=data_url.data_path(),
        data_slice=data_url.data_slice(),
    )

    _, ext = os.path.splitext(data_url.file_path())
    ext = ext.lower()
    if ext in (".h5", ".hdf5", ".nx", ".nxs", ".nexus"):
        params["scheme"] = "silx"
    elif ext in (".edf", ".tif", ".tiff"):
        if data_url.data_path():
            params["scheme"] = "silx"
        else:
            params["scheme"] = "fabio"
    else:
        params["scheme"] = "ascii"
    return DataUrl(**params)


_ASCII_SCHEMES = ("ascii", "spec", "pymca", "pymca5", "larch", "xraylarch")
