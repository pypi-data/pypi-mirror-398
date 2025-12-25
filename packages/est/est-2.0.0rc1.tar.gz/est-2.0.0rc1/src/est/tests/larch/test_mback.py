import pytest

from ...core.types.xasobject import XASObject

try:
    import larch
except ImportError:
    larch = None
else:
    from ...core.process.larch.mback import larch_mback
    from ...core.process.larch.mback import process_spectr_mback


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_single_spectrum(spectrum_cu_from_larch):
    """Make sure computation on one spectrum is valid"""
    configuration = {"z": 29}
    assert spectrum_cu_from_larch.normalized_mu is None
    process_spectr_mback(spectrum_cu_from_larch, configuration)
    assert spectrum_cu_from_larch.normalized_mu is not None


@pytest.fixture()
def xas_object(spectrum_cu_from_larch):
    configuration = {"z": 29}
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
    res = larch_mback(xas_object, mback_config={"z": 29})
    assert isinstance(res, XASObject)
    spectrum0 = res.spectra.data.flat[0]
    assert spectrum0.normalized_mu is not None


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra_asdict(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    res = larch_mback(xas_object.to_dict(), mback_config={"z": 29})
    assert isinstance(res, XASObject)
    spectrum0 = res.spectra.data.flat[0]
    assert spectrum0.normalized_mu is not None
