"""
Tests for reading spectra with different dimensions organisation
(X, Y, Channels), (Channels, Y, X), (Y, Channels, X)
"""

import warnings

import h5py
import numpy
import pytest
from silx.io.url import DataUrl

from ..core.io.read_xas import read_from_url
from ..core.types.xasobject import XASObject
from ..core.units import ur


@pytest.fixture()
def testDimensionsXYEnergy(tmpdir):
    """Test that spectra stored as X, Y Energy can be read"""
    x_dim = 4
    y_dim = 2
    energy_dim = 3
    shape = (x_dim, y_dim, energy_dim)
    spectra = numpy.arange(x_dim * y_dim * energy_dim).reshape(shape)
    channel = numpy.linspace(0, 1, energy_dim)
    spectra_url = saveSpectra(tmpdir, spectra)
    channel_url = saveChannel(tmpdir, channel=channel)

    # if dims are incoherent with energy, should raise an error
    dims = (2, 1, 0)
    with pytest.raises(ValueError):
        read_from_url(spectra_url=spectra_url, channel_url=channel_url, dimensions=dims)
    dims = (0, 1, 2)
    xas_obj = read_from_url(
        spectra_url=spectra_url, channel_url=channel_url, dimensions=dims
    )
    assert isinstance(xas_obj, XASObject)
    assert xas_obj.n_spectrum == x_dim * y_dim
    numpy.testing.assert_array_equal(xas_obj.spectra.data.flat[1].mu, spectra[1, 0, :])
    numpy.testing.assert_array_equal(xas_obj.spectra.data.flat[2].energy, channel)


@pytest.fixture()
def testDimensionsChannelYX(tmpdir):
    """Test that spectra stored as Energy, Y, X can be read"""
    x_dim = 10
    y_dim = 5
    energy_dim = 30
    shape = (energy_dim, y_dim, x_dim)
    spectra = numpy.arange(x_dim * y_dim * energy_dim).reshape(shape)
    channel = numpy.linspace(0, 100, energy_dim)
    spectra_url = saveSpectra(tmpdir, spectra)
    channel_url = saveChannel(tmpdir, channel=channel)

    # if dims are incoherent with energy, should raise an error
    dims = (0, 1, 2)
    with warnings.catch_warnings(record=True):
        read_from_url(spectra_url=spectra_url, channel_url=channel_url, dimensions=dims)

    dims = (2, 1, 0)
    xas_obj = read_from_url(
        spectra_url=spectra_url, channel_url=channel_url, dimensions=dims
    )
    assert isinstance(xas_obj, XASObject)
    assert xas_obj.n_spectrum == x_dim * y_dim
    numpy.testing.assert_array_equal(xas_obj.spectra.data.flat[1].mu, spectra[:, 0, 1])
    numpy.testing.assert_array_equal(
        xas_obj.spectra.data.flat[2].energy, (channel * ur.eV).m
    )


def saveSpectra(tmpdir, spectra):
    """Save the spectra to the spectra file defined in setup and return the
    associated silx url"""
    filename = str(tmpdir / "myfile.h5")
    data_path = "/data/NXdata/data"
    with h5py.File(filename, "a") as f:
        f[data_path] = spectra

    return DataUrl(file_path=filename, data_path=data_path, scheme="silx")


def saveChannel(tmpdir, channel):
    """Save the energy to the spectra file defined in setup and return the
    associated silx url"""
    filename = str(tmpdir / "myfile.h5")
    data_path = "/data/NXdata/channel"
    with h5py.File(filename, "a") as f:
        f[data_path] = channel

    return DataUrl(file_path=filename, data_path=data_path, scheme="silx")
