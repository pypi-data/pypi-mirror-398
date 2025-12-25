import h5py
import pytest
from silx.io.url import DataUrl

from ...core.io.read_xas import read_from_url
from ...core.types.xasobject import XASObject
from ..data import example_spectra

try:
    import PyMca5
except ImportError:
    PyMca5 = None
else:
    from ...core.process.pymca.normalization import pymca_normalization


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    xas_obj = XASObject(
        spectra=(spectrum_cu_from_pymca,),
        energy=spectrum_cu_from_pymca.energy,
        dim1=1,
        dim2=1,
    )
    res_spectrum = xas_obj.spectra.data.flat[0]
    assert res_spectrum.normalized_energy is None
    assert res_spectrum.normalized_mu is None
    assert res_spectrum.post_edge is None
    pymca_normalization(xas_obj=xas_obj)
    assert xas_obj.normalized_energy is not None
    assert res_spectrum.normalized_energy is not None
    assert res_spectrum.normalized_mu is not None
    assert res_spectrum.post_edge is not None


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum_asdict(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    xas_obj = XASObject(
        spectra=(spectrum_cu_from_pymca,),
        energy=spectrum_cu_from_pymca.energy,
        dim1=1,
        dim2=1,
    )
    res_spectrum = xas_obj.spectra.data.flat[0]
    assert res_spectrum.normalized_energy is None
    assert res_spectrum.normalized_mu is None
    assert res_spectrum.post_edge is None
    xas_obj = pymca_normalization(xas_obj=xas_obj.to_dict())
    res_spectrum = xas_obj.spectra.data.flat[0]
    assert xas_obj.normalized_energy is not None
    assert res_spectrum.normalized_energy is not None
    assert res_spectrum.normalized_mu is not None
    assert res_spectrum.post_edge is not None


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_multiple_spectra(tmpdir):
    """Make sure computation on spectra is valid (n spectrum)"""
    energy, spectra = example_spectra(shape=(256, 20, 10))
    spectra_path = "/data/NXdata/data"
    energy_path = "/data/NXdata/energy"
    filename = str(tmpdir / "myfile.h5")
    with h5py.File(filename, "a") as f:
        f[spectra_path] = spectra
        f[energy_path] = energy

    xas_obj = read_from_url(
        spectra_url=DataUrl(file_path=filename, data_path=spectra_path, scheme="silx"),
        channel_url=DataUrl(file_path=filename, data_path=energy_path, scheme="silx"),
        dimensions=(2, 1, 0),
    )

    pymca_normalization(xas_obj=xas_obj)
    for spectrum in xas_obj.spectra.data.flat:
        assert spectrum.normalized_mu is not None
        assert spectrum.normalized_energy is not None
        assert spectrum.post_edge is not None
