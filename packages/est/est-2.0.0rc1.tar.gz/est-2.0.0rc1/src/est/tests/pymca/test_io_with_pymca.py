import h5py
import numpy

from ...core.io.read_xas import build_ascii_data_url
from ...core.io.read_xas import read_from_url
from ...core.io.write_xas import write_xas
from ...core.types.xasobject import XASObject
from ..data import example_spectra


def test_read_spectrum(filename_cu_from_pymca):
    """Test read function for spectra and configuration"""
    res = read_from_url(
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca,
            col_name="Column 1",
            scan_title=None,
            data_slice=None,
        ),
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca,
            col_name="Column 2",
            scan_title=None,
            data_slice=None,
        ),
    )
    assert isinstance(res, XASObject)
    assert res.n_spectrum == 1
    spectrum_0 = res.spectra.data.flat[0]
    assert spectrum_0.mu is not None
    assert spectrum_0.energy is not None


def test_nx_writing(tmpdir):
    """Test that the nx process is correctly store ad the output data"""
    energy, spectra = example_spectra(shape=(256, 20, 10))
    xas_obj = XASObject(spectra=spectra, energy=energy, dim1=20, dim2=10)
    h5_file = str(tmpdir / "output_file.h5")

    write_xas(h5_file, xas_obj)
    with h5py.File(h5_file, "r") as hdf:
        assert "scan1" in hdf.keys()
        assert "data" in hdf["scan1"].keys()
        assert "absorbed_beam" in hdf["scan1"].keys()
        assert "monochromator" in hdf["scan1"].keys()

    loaded_xas_obj = XASObject.from_file(h5_file)
    numpy.testing.assert_allclose(loaded_xas_obj.energy, xas_obj.energy)
    numpy.testing.assert_allclose(
        loaded_xas_obj.absorbed_beam(), xas_obj.absorbed_beam()
    )
