import pytest

try:
    import larch
except ImportError:
    larch = None
else:
    from ...core.process.larch.autobk import larch_autobk
    from ...core.process.larch.autobk import process_spectr_autobk
    from ...core.types.xasobject import XASObject


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_single_spectrum(spectrum_cu_from_larch):
    configuration = {"kweight": 1}
    assert spectrum_cu_from_larch.k is None
    assert spectrum_cu_from_larch.chi is None
    process_spectr_autobk(spectrum_cu_from_larch, configuration)
    assert spectrum_cu_from_larch.k is not None
    assert spectrum_cu_from_larch.chi is not None


@pytest.fixture()
def xas_object(spectrum_cu_from_larch):
    configuration = {"kweight": 1}
    return XASObject(
        spectra=(spectrum_cu_from_larch,),
        energy=spectrum_cu_from_larch.energy,
        dim1=1,
        dim2=1,
        configuration=configuration,
    )


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    res = larch_autobk(xas_object)
    assert isinstance(res, XASObject)
    spectrum0 = res.spectra.data.flat[0]
    assert hasattr(spectrum0, "k")
    assert hasattr(spectrum0, "chi")


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra_as_dict(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    res = larch_autobk(xas_object.to_dict())
    assert isinstance(res, XASObject)
    spectrum0 = res.spectra.data.flat[0]
    assert hasattr(spectrum0, "k")
    assert hasattr(spectrum0, "chi")
