import pytest

from ...core.types.xasobject import XASObject

try:
    import larch
except ImportError:
    larch = None
else:
    from ...core.process.larch.mback_norm import larch_mback_norm
    from ...core.process.larch.mback_norm import process_spectr_mback_norm
    from ...core.process.larch.pre_edge import process_spectr_pre_edge


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_single_spectrum(spectrum_cu_from_larch):
    """Make sure computation on one spectrum is valid"""
    process_spectr_pre_edge(
        spectrum=spectrum_cu_from_larch, overwrite=True, configuration={}
    )
    assert spectrum_cu_from_larch.normalized_mu is not None
    configuration = {"z": 29}

    process_spectr_mback_norm(spectrum_cu_from_larch, configuration)
    assert spectrum_cu_from_larch.normalized_mu is not None


@pytest.fixture()
def xas_object(spectrum_cu_from_larch):
    configuration = {"z": 29}
    process_spectr_pre_edge(
        spectrum=spectrum_cu_from_larch, overwrite=True, configuration={}
    )
    assert spectrum_cu_from_larch.normalized_mu is not None
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
    res = larch_mback_norm(xas_object)
    assert isinstance(res, XASObject)
    spectrum0 = res.spectra.data.flat[0]
    assert spectrum0.normalized_mu is not None


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra_asdict(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    res = larch_mback_norm(xas_object.to_dict())
    assert isinstance(res, XASObject)
    spectrum0 = res.spectra.data.flat[0]
    assert spectrum0.normalized_mu is not None
