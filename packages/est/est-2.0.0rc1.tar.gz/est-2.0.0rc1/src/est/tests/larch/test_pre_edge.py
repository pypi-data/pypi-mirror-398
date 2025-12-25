import pytest

from ...core.types.xasobject import XASObject

try:
    import larch
except ImportError:
    larch = None
else:
    from ...core.process.larch.pre_edge import larch_pre_edge
    from ...core.process.larch.pre_edge import process_spectr_pre_edge


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_single_spectrum(spectrum_cu_from_larch):
    """Make sure computation on one spectrum is valid"""
    configuration = {}
    assert spectrum_cu_from_larch.pre_edge is None
    assert spectrum_cu_from_larch.e0 is None
    process_spectr_pre_edge(spectrum_cu_from_larch, configuration)
    assert spectrum_cu_from_larch.pre_edge is not None
    assert spectrum_cu_from_larch.e0 is not None


@pytest.fixture()
def xas_object(spectrum_cu_from_larch):
    configuration = {}
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
    spectrum0 = xas_object.spectra.data.flat[0]
    assert spectrum0.pre_edge is None
    assert spectrum0.e0 is None
    larch_pre_edge(xas_object)
    assert spectrum0.pre_edge is not None
    assert spectrum0.e0 is not None


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def test_multiple_spectra_asdict(xas_object):
    """Make sure computation on spectra is valid (n spectrum)"""
    spectrum0 = xas_object.spectra.data.flat[0]
    assert spectrum0.pre_edge is None
    assert spectrum0.e0 is None
    xas_object = larch_pre_edge(xas_object.to_dict())
    spectrum0 = xas_object.spectra.data.flat[0]
    assert spectrum0.pre_edge is not None
    assert spectrum0.e0 is not None
