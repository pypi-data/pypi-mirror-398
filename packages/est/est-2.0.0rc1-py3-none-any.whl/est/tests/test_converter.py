"""Test conversion of xas_object to Orange.data.Table"""

import pytest

try:
    import Orange
except ImportError:
    Orange = None
else:
    import numpy

    from ..core.types.xasobject import XASObject
    from ..core.utils.converter import Converter
    from .data import example_spectra


@pytest.mark.skipif(Orange is None, reason="Orange3 is not installed")
def test_conversion():
    """Make sure the conversion to/from Orange.data.Table is safe for energy
    and beam absorption
    """

    energy, spectra = example_spectra(shape=(128, 20, 10))
    xas_object = XASObject(energy=energy, spectra=spectra, dim1=20, dim2=10)

    xas_object = xas_object.copy()
    data_table = Converter.toDataTable(xas_object=xas_object)
    converted_xas_object = Converter.toXASObject(data_table=data_table)
    numpy.testing.assert_array_almost_equal(
        xas_object.energy, converted_xas_object.energy
    )
    numpy.testing.assert_array_almost_equal(
        xas_object.spectra.data.flat[0].mu,
        converted_xas_object.spectra.data.flat[0].mu,
    )
    numpy.testing.assert_array_almost_equal(
        xas_object.spectra.data.flat[5].mu,
        converted_xas_object.spectra.data.flat[5].mu,
    )
    numpy.testing.assert_array_almost_equal(
        xas_object.spectra.data.flat[18].mu,
        converted_xas_object.spectra.data.flat[18].mu,
    )
