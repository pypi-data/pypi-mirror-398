"""Test the spectrum class"""

from ..core.types.xasobject import XASObject
from .data import example_spectra


def test_from_dat(spectrum_cu_from_pymca):
    """check that we can create a Spectrum from a pymca .dat file"""
    assert spectrum_cu_from_pymca.energy is not None
    assert spectrum_cu_from_pymca.mu is not None


def test_from_mock():
    """check that we can create a Spectrum from numpy arrays"""
    energy, spectra = example_spectra(shape=(256, 20, 10))
    xas_obj = XASObject(spectra=spectra, energy=energy, dim1=20, dim2=10)
    spectra = xas_obj.spectra
    assert xas_obj.n_spectrum == 20 * 10
    assert xas_obj.n_spectrum == 20 * 10
    assert spectra.data.flat[0] == spectra[0, 0]
    spectra.as_ndarray("mu")
