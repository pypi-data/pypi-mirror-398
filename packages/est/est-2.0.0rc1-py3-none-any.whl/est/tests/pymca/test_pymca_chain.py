"""
unit test for workflow composed of pymca process
"""

import h5py
import numpy
import pytest

from ...core.io.read_xas import build_ascii_data_url
from ...core.io.read_xas import read_from_url
from ...core.io.write_xas import write_xas
from ...core.process.roi import xas_roi
from ...core.types.xasobject import XASObject
from ..data import example_spectra

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
def test_pymca_process(filename_cu_from_pymca):
    """Make sure the process have valid io"""
    exafs_configuration = {
        "Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]},
        "KMin": 0,
        "KMax": 2.3,
    }

    out = read_from_url(
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca,
            col_name="Column 2",
            scan_title=None,
            data_slice=None,
        ),
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca,
            col_name="Column 1",
            scan_title=None,
            data_slice=None,
        ),
    )
    out.configuration = {"EXAFS": exafs_configuration, "SET_KWEIGHT": 0}
    out = pymca_normalization(out)
    out = pymca_exafs(out)
    out = pymca_k_weight(out)
    out = pymca_ft(out)
    assert isinstance(out, XASObject)


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_pymca_process_with_dict(filename_cu_from_pymca):
    """Make sure the process have valid io"""
    exafs_configuration = {
        "Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]},
        "KMin": 0,
        "KMax": 2.3,
    }

    out = read_from_url(
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca,
            col_name="Column 2",
            scan_title=None,
            data_slice=None,
        ),
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca,
            col_name="Column 1",
            scan_title=None,
            data_slice=None,
        ),
    )
    out.configuration = {"EXAFS": exafs_configuration, "SET_KWEIGHT": 0}
    out = pymca_normalization(out.to_dict())
    out = pymca_exafs(out.to_dict())
    out = pymca_k_weight(out.to_dict())
    out = pymca_ft(out.to_dict())
    assert isinstance(out, XASObject)
    assert out.spectra.data.flat[0].ft is not None
    assert len(out.spectra.data.flat[0].ft.intensity) > 0


@pytest.mark.parametrize(
    "roi_size, expected_shape", [((1, 5), (5, 1)), ((-1, -1), (20, 10))]
)
@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_pymca_with_roi(roi_size, expected_shape):
    """Make sure the process have valid io"""
    exafs_configuration = {
        "Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]},
        "KMin": 0,
        "KMax": 2.3,
    }
    energy, spectra = example_spectra(shape=(256, 20, 10))
    xas_obj = XASObject(
        spectra=spectra,
        energy=energy,
    )
    dict_xas_obj = xas_obj.to_dict()
    assert "spectra" in dict_xas_obj.keys()
    assert "energy" in dict_xas_obj.keys()

    tmp_obj = XASObject.from_dict(dict_xas_obj)
    numpy.testing.assert_array_equal(
        tmp_obj.energy, tmp_obj.spectra.data.flat[0].energy
    )
    out = xas_roi(dict_xas_obj, roi_origin=(0, 2), roi_size=roi_size)
    out.configuration = {"EXAFS": exafs_configuration, "SET_KWEIGHT": 0}
    out = pymca_normalization(out)
    out = pymca_exafs(out)
    out = pymca_k_weight(out)
    out = pymca_ft(out)
    assert isinstance(out, XASObject)
    assert out.spectra.shape == expected_shape
    assert out.spectra.data.flat[0].ft is not None
    assert len(out.spectra.data.flat[0].ft.intensity) > 0


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_save_workflow(tmpdir):
    """Test that the XASObject will saved some results from processes 'write_xas'"""
    energy, spectra = example_spectra(shape=(100, 10, 10))
    assert spectra.shape == (100, 10, 10)
    assert len(energy) == spectra.shape[0]
    xas_obj = XASObject(spectra=spectra, energy=energy, dim1=10, dim2=10)

    h5_file = str(tmpdir / "output_file.h5")

    out = pymca_normalization(xas_obj)
    configuration = {
        "Knots": {"Values": (1, 2, 5), "Number": 3, "Orders": [3, 3, 3]},
        "KMin": 0,
        "KMax": 2.3,
    }
    out = pymca_exafs(out, exafs=configuration)
    out = pymca_k_weight(out, k_weight=0)
    out = pymca_ft(out)
    out = pymca_normalization(out)

    write_xas(h5_file, out)

    with h5py.File(h5_file, "r") as hdf:
        assert "scan1" in hdf.keys()
        assert "data" in hdf["scan1"].keys()
        assert "absorbed_beam" in hdf["scan1"].keys()
        assert "monochromator" in hdf["scan1"].keys()
