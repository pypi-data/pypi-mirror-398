import pytest

try:
    import PyMca5
except ImportError:
    PyMca5 = None
else:
    from ...core.process.pymca.exafs import pymca_exafs
    from ...core.process.pymca.normalization import pymca_normalization

from ...core.types.xasobject import XASObject


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    exafs_configuration = {"Knots": {"Values": (1, 2, 5), "Number": 3}}
    configuration = {"EXAFS": exafs_configuration}
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        dim1=1,
        dim2=1,
        configuration=configuration,
    )

    # first process normalization
    for spectrum in xas_obj.spectra.data.flat:
        assert spectrum.pre_edge is None
    pymca_normalization(xas_obj=xas_obj)
    for spectrum in xas_obj.spectra.data.flat:
        assert spectrum.pre_edge is not None

    pymca_exafs(xas_obj)
    spectrum_0 = xas_obj.spectra.data.flat[0]
    assert spectrum_0.k is not None
    assert spectrum_0.chi is not None
    assert spectrum_0.pymca_dict.PostEdgeB is not None


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_single_spectrum_asdict(spectrum_cu_from_pymca):
    """Make sure the process is processing correctly on a spectrum"""
    exafs_configuration = {"Knots": {"Values": (1, 2, 5), "Number": 3}}
    configuration = {"EXAFS": exafs_configuration}
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        dim1=1,
        dim2=1,
        configuration=configuration,
    )

    spectrum_0 = xas_obj.spectra.data.flat[0]
    # first process normalization
    assert spectrum_0.pre_edge is None
    xas_obj = pymca_normalization(xas_obj=xas_obj.to_dict())
    spectrum_0 = xas_obj.spectra.data.flat[0]
    assert spectrum_0.pre_edge is not None

    xas_obj = pymca_exafs(xas_obj.to_dict())
    spectrum_0 = xas_obj.spectra.data.flat[0]
    assert spectrum_0.k is not None
    assert spectrum_0.chi is not None
    assert spectrum_0.pymca_dict.PostEdgeB is not None
