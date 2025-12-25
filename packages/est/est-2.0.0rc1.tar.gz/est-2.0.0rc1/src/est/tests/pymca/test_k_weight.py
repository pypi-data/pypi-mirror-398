import pytest

from ...core.types.xasobject import XASObject

try:
    import PyMca5
except ImportError:
    PyMca5 = None
else:
    from ...core.process.pymca.k_weight import pymca_k_weight
    from ...core.process.pymca.normalization import pymca_normalization


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    config = {
        "SET_KWEIGHT": 2.0,
        "EXAFS": {"Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]}},
    }
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        configuration=config,
        dim1=1,
        dim2=1,
    )
    xas_obj = pymca_normalization(xas_obj)
    pymca_k_weight(xas_obj=xas_obj)


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum_asdict(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    config = {
        "SET_KWEIGHT": 2.0,
        "EXAFS": {"Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]}},
    }
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        configuration=config,
        dim1=1,
        dim2=1,
    )
    xas_obj = pymca_normalization(xas_obj)
    pymca_k_weight(xas_obj=xas_obj.to_dict())
