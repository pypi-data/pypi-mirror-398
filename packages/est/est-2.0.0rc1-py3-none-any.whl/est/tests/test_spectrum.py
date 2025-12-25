"""Test the spectrum class"""

import numpy

from ..core.types.spectrum import Spectrum
from ..core.units import ur


def test_from_dat(spectrum_cu_from_pymca):
    """check that we can create a Spectrum from a pymca .dat file"""
    assert spectrum_cu_from_pymca.energy is not None
    assert spectrum_cu_from_pymca.mu is not None


def test_from_numpy_array():
    """check that we can create a Spectrum from numpy arrays"""
    energy = numpy.arange(10, 20)
    mu = numpy.arange(10)
    spectrum = Spectrum(energy=energy, mu=mu)
    numpy.testing.assert_array_equal(spectrum.energy, (energy * ur.eV).m)
    numpy.testing.assert_array_equal(spectrum.mu, mu)
    mu_2 = numpy.arange(30, 40)
    spectrum.mu = mu_2
    numpy.testing.assert_array_equal(spectrum.mu, mu_2)
