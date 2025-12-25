import pytest

from ...core.types.xasobject import XASObject

try:
    import PyMca5
except ImportError:
    PyMca5 = None
else:
    from ...core.process.pymca.exafs import pymca_exafs
    from ...core.process.pymca.ft import pymca_ft
    from ...core.process.pymca.k_weight import pymca_k_weight
    from ...core.process.pymca.normalization import pymca_normalization


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        dim1=1,
        dim2=1,
    )
    xas_obj = pymca_normalization(xas_obj=xas_obj)
    xas_obj = pymca_exafs(xas_obj=xas_obj)
    xas_obj = pymca_k_weight(xas_obj=xas_obj)
    res = pymca_ft(xas_obj=xas_obj)
    assert isinstance(res, XASObject)
    assert res.spectra.data.flat[0].ft.radius is not None
    assert res.spectra.data.flat[0].ft.imaginary is not None
    assert res.spectra.data.flat[0].ft.intensity is not None


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum_asdict(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        dim1=1,
        dim2=1,
    )
    xas_obj = pymca_normalization(xas_obj=xas_obj)
    xas_obj = pymca_exafs(xas_obj=xas_obj)
    xas_obj = pymca_k_weight(xas_obj=xas_obj)
    res = pymca_ft(xas_obj=xas_obj.to_dict())
    assert isinstance(res, XASObject)
    assert res.spectra.data.flat[0].ft.radius is not None
    assert res.spectra.data.flat[0].ft.imaginary is not None
    assert res.spectra.data.flat[0].ft.intensity is not None
