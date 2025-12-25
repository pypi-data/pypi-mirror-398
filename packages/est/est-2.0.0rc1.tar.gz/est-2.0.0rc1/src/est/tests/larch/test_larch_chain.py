import numpy
import pytest

try:
    import larch
except ImportError:
    larch = None
else:
    from ...core.process.larch.autobk import process_spectr_autobk as autobk
    from ...core.process.larch.pre_edge import process_spectr_pre_edge as pre_edge
    from ...core.process.larch.xftf import process_spectr_xftf as xftf


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def testAutobk(spectrum_cu_from_larch):
    """equivalent treatment as the 'xafs.autobk.par script from larch'"""
    pre_edge(
        spectrum=spectrum_cu_from_larch,
        overwrite=True,
        configuration={"rbkg": 1.0, "kweight": 2},
    )
    autobk(
        spectrum=spectrum_cu_from_larch,
        overwrite=True,
        configuration={
            "kmin": 2,
            "kmax": 16,
            "dk": 3,
            "window": "hanning",
            "kweight": 2,
        },
    )
    xftf(spectrum=spectrum_cu_from_larch, overwrite=True, configuration={"kweight": 2})


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def testAutobkLimitedData(limited_data_spectrum):
    pre_edge(
        spectrum=limited_data_spectrum,
        overwrite=True,
        configuration={"rbkg": 1.0, "kweight": 2},
    )
    autobk(
        spectrum=limited_data_spectrum,
        overwrite=True,
        configuration={
            "kmin": 2,
            "kmax": 16,
            "dk": 3,
            "window": "hanning",
            "kweight": 2,
        },
    )
    xftf(spectrum=limited_data_spectrum, overwrite=True, configuration={"kweight": 2})


@pytest.mark.skipif(larch is None, reason="xraylarch not installed")
def testXafsft1(spectrum_cu_from_larch):
    """equivalent treatment as the 'xafs.doc_xafs1.par script from larch'"""
    autobk(
        spectrum=spectrum_cu_from_larch,
        overwrite=True,
        configuration={"rbkg": 1.0, "kweight": 2, "clamp+hi": 10},
    )
    assert spectrum_cu_from_larch.k is not None
    assert spectrum_cu_from_larch.chi is not None
    conf, spec_dk1 = xftf(
        spectrum=spectrum_cu_from_larch,
        overwrite=False,
        configuration={
            "kweight": 2,
            "kmin": 3,
            "kmax": 13,
            "window": "hanning",
            "dk": 1,
        },
    )
    conf, spec_dk2 = xftf(
        spectrum=spectrum_cu_from_larch,
        overwrite=False,
        configuration={
            "kweight": 2,
            "kmin": 3,
            "kmax": 13,
            "window": "hanning",
            "dk": 5,
        },
    )
    # TODO: handle numpy arrays
    # assert spec_dk1.model_dump() != spec_dk2.model_dump()
    assert not numpy.array_equal(spec_dk1.ft.real, spec_dk2.ft.real)
