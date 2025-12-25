import pytest

from ...core.types.xasobject import XASObject

try:
    import larch
except ImportError:
    larch = None
else:
    from ...core.process.larch.autobk import process_spectr_autobk
    from ...core.process.larch.xftf import larch_xftf
    from ...core.process.larch.xftf import process_spectr_xftf


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_single_spectrum(spectrum_cu_from_larch):
    """Make sure computation on one spectrum is valid"""
    configuration = {
        "window": "hanning",
        "kweight": 2,
        "kmin": 3,
        "kmax": 13,
        "dk": 1,
    }
    # for xftf we need to compute pre edge before
    process_spectr_autobk(spectrum_cu_from_larch, configuration={}, overwrite=True)
    assert spectrum_cu_from_larch.k is not None
    assert spectrum_cu_from_larch.chi is not None

    process_spectr_xftf(spectrum_cu_from_larch, configuration, overwrite=True)
    assert spectrum_cu_from_larch.ft.radius is not None
    assert spectrum_cu_from_larch.ft.real is not None
    assert spectrum_cu_from_larch.ft.imaginary is not None
    assert spectrum_cu_from_larch.ft.intensity is not None


@pytest.fixture()
def xas_object(spectrum_cu_from_larch):
    configuration = {"z": 29}
    process_spectr_autobk(spectrum_cu_from_larch, configuration={}, overwrite=True)
    xas_object = XASObject(
        spectra=(spectrum_cu_from_larch,),
        energy=spectrum_cu_from_larch.energy,
        dim1=1,
        dim2=1,
        configuration=configuration,
    )
    # for xftf we need to compute pre edge before
    spectrum = xas_object.spectra.data.flat[0]
    assert spectrum.k is not None
    assert spectrum.chi is not None
    return xas_object


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    res = larch_xftf(xas_object)
    assert isinstance(res, XASObject)
    spectrum = res.spectra.data.flat[0]
    assert spectrum.ft.radius is not None
    assert spectrum.ft.real is not None
    assert spectrum.ft.imaginary is not None
    assert spectrum.ft.intensity is not None


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra_asdict(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    res = larch_xftf(xas_object.to_dict())
    assert isinstance(res, XASObject)
    spectrum = res.spectra.data.flat[0]
    assert spectrum.ft.radius is not None
    assert spectrum.ft.real is not None
    assert spectrum.ft.imaginary is not None
    assert spectrum.ft.intensity is not None
