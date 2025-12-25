"""
Test manually chaining of processes
"""

import pytest

from ..core.io.write_xas import write_xas
from ..core.types.xasobject import XASObject

try:
    import larch
except ImportError:
    larch = None
else:
    from ..core.process.larch.autobk import larch_autobk
    from ..core.process.larch.pre_edge import larch_pre_edge
    from ..core.process.larch.xftf import larch_xftf

try:
    import PyMca5
except ImportError:
    PyMca5 = None
else:
    from ..core.process.pymca.exafs import pymca_exafs
    from ..core.process.pymca.ft import pymca_ft
    from ..core.process.pymca.k_weight import pymca_k_weight
    from ..core.process.pymca.normalization import pymca_normalization


@pytest.fixture()
def chain_input(spectrum_cu_from_pymca):
    xas_obj = XASObject(
        energy=spectrum_cu_from_pymca.energy,
        spectra=(spectrum_cu_from_pymca,),
        dim1=1,
        dim2=1,
    )
    configuration_exafs = {
        "Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]},
        "KMin": 0,
        "KMax": 2.3,
    }
    return xas_obj, configuration_exafs


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
@pytest.mark.skipif(larch is None, reason="larch is not installed")
def test_chain_normalize_autobk_kweight_ft(chain_input):
    """Test the following chain of process:
    pymca normalize -> larch autobk -> kweight -> pymca ft
    """
    xas_obj, configuration_exafs = chain_input
    xas_obj.configuration = {"EXAFS": configuration_exafs}
    # pymca normalization
    xas_obj = pymca_normalization(xas_obj)
    # larch autobk
    xas_obj = larch_autobk(xas_obj)
    # k weight
    xas_obj = pymca_k_weight(xas_obj, k_weight=0)
    # pymca ft
    xas_obj = pymca_ft(xas_obj)

    assert xas_obj.spectra.data.flat[0].ft.intensity is not None
    assert len(xas_obj.spectra.data.flat[0].ft.intensity) > 1


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
@pytest.mark.skipif(larch is None, reason="larch is not installed")
def test_chain_preedge_exafs_xftf(chain_input, tmpdir):
    """Test the following chain of process:
    larch pre_edge -> pymca exafs -> larch xftf
    """
    xas_obj, configuration_exafs = chain_input
    # larch pre edge
    xas_obj = larch_pre_edge(xas_obj)
    # pymca exafs
    xas_obj = pymca_exafs(xas_obj, exafs=configuration_exafs)

    # for now we cannot link xftf because chi is not set by pymca exafs
    spectrum_0 = xas_obj.spectra.data.flat[0]
    assert spectrum_0.post_edge is not None
    assert spectrum_0.chi is not None
    assert spectrum_0.k is not None

    # larch xftf
    xas_obj = larch_xftf(xas_obj)

    write_xas(str(tmpdir / "output_file.h5"), xas_obj)
