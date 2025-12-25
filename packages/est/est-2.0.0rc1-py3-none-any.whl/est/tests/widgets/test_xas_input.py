import h5py
import numpy
import pytest
from silx.io.url import DataUrl

from ...core.units import ur
from ..data import example_spectrum

try:
    import larch
except ImportError:
    larch = None

from orangecontrib.est.widgets.utils.xas_input import XASInputOW

from ...core.io._utils.load import load_data
from ...core.io.information import InputInformation
from ...core.io.read_xas import build_ascii_data_url


def test_xas_input_no_dataset(qtapp):
    """Check behavior if no settings exists"""
    widget = XASInputOW()
    assert widget.buildXASObj() is None
    widget.loadSettings(input_information=None)
    while qtapp.hasPendingEvents():
        qtapp.processEvents()
    assert widget.buildXASObj() is None


def test_xas_input_with_spec(qtapp, filename_cu_from_pymca, spectrum_cu_from_pymca):
    """Check behavior when a spec file is provided"""
    energy_url = build_ascii_data_url(
        file_path=str(filename_cu_from_pymca),
        col_name="Column 1",
    )
    spectra_url = build_ascii_data_url(
        file_path=str(filename_cu_from_pymca),
        col_name="Column 2",
    )
    input_information = InputInformation(
        spectra_url=spectra_url,
        channel_url=energy_url,
    )
    widget = XASInputOW()
    assert widget.buildXASObj() is None
    widget.loadSettings(input_information=input_information)
    while qtapp.hasPendingEvents():
        qtapp.processEvents()
    xas_obj = widget.buildXASObj()

    numpy.testing.assert_almost_equal(
        xas_obj.get_spectrum(0, 0).mu, spectrum_cu_from_pymca.mu
    )
    numpy.testing.assert_almost_equal(xas_obj.energy, spectrum_cu_from_pymca.energy)


@pytest.mark.skipif(larch is None, reason="larch is not installed")
def test_xas_input_xmu(qtapp, filename_cu_from_larch):
    input_information = InputInformation(
        spectra_url=DataUrl(
            file_path=str(filename_cu_from_larch),
            data_path=None,
            scheme="larch",
        )
    )
    widget = XASInputOW()
    assert widget.buildXASObj() is None
    widget.loadSettings(input_information=input_information)
    while qtapp.hasPendingEvents():
        qtapp.processEvents()
    xas_obj = widget.buildXASObj()
    assert xas_obj is not None


def test_xas_input_hdf5(qtapp, hdf5_filename_cu_from_pymca):
    """
    Check behavior if we provide to the widget some valid inputs
    """
    energy_url = DataUrl(
        file_path=str(hdf5_filename_cu_from_pymca),
        data_path="/1.1/instrument/energy/value",
        scheme="silx",
    )
    spectra_url = DataUrl(
        file_path=str(hdf5_filename_cu_from_pymca),
        data_path="/1.1/instrument/mu/data",
        scheme="silx",
    )
    input_information = InputInformation(
        spectra_url=spectra_url,
        channel_url=energy_url,
    )
    widget = XASInputOW()
    assert widget.buildXASObj() is None
    widget.loadSettings(input_information=input_information)
    while qtapp.hasPendingEvents():
        qtapp.processEvents()
    xas_obj = widget.buildXASObj()

    numpy.testing.assert_almost_equal(
        xas_obj.get_spectrum(0, 0).mu, load_data(spectra_url)
    )
    expected = load_data(energy_url).m_as(ur.eV)
    numpy.testing.assert_almost_equal(xas_obj.energy, expected)


@pytest.mark.parametrize("direction", ["uni", "bi"])
def test_xas_input_hdf5_concatenated(qtapp, tmpdir, direction):
    energy, mu = example_spectrum(5000, 5500, 100)

    full_energy = numpy.zeros((4, len(energy)))
    full_mu = numpy.zeros((4, len(energy)))
    full_energy[0] = energy[:]
    full_mu[0] = mu[:]
    if direction == "bi":
        full_energy[1] = energy[::-1]
        full_mu[1] = mu[::-1]
    else:
        full_energy[1] = energy[:]
        full_mu[1] = mu[:]
    full_energy[2] = energy[:]
    full_mu[2] = mu[:]
    if direction == "bi":
        full_energy[3] = energy[::-1]
        full_mu[3] = mu[::-1]
    else:
        full_energy[3] = energy[:]
        full_mu[3] = mu[:]

    tmpfilename = tmpdir / "test.h5"

    with h5py.File(tmpfilename, "w") as h5file:
        h5file["energy"] = full_energy.flatten()
        h5file["mu"] = full_mu.flatten()

    energy_url = DataUrl(
        file_path=str(tmpfilename),
        data_path="energy",
        scheme="silx",
    )
    spectra_url = DataUrl(
        file_path=str(tmpfilename),
        data_path="mu",
        scheme="silx",
    )
    input_information = InputInformation(
        spectra_url=spectra_url, channel_url=energy_url, is_concatenated=True
    )
    widget = XASInputOW()
    assert widget.buildXASObj() is None
    widget.loadSettings(input_information=input_information)
    while qtapp.hasPendingEvents():
        qtapp.processEvents()
    xas_obj = widget.buildXASObj()

    assert xas_obj is not None
    numpy.testing.assert_almost_equal(xas_obj.energy, energy)
    numpy.testing.assert_almost_equal(xas_obj.get_spectrum(0, 0).mu, mu)
    numpy.testing.assert_almost_equal(xas_obj.get_spectrum(1, 0).mu, mu)
    numpy.testing.assert_almost_equal(xas_obj.get_spectrum(2, 0).mu, mu)
    numpy.testing.assert_almost_equal(xas_obj.get_spectrum(3, 0).mu, mu)
