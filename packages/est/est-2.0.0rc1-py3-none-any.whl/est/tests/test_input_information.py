import numpy
from silx.io import h5py_utils
from silx.io.url import DataUrl

from ..core.io._utils.ascii import split_ascii_url
from ..core.io.information import InputInformation
from ..core.io.read_xas import build_ascii_data_url
from ..core.io.read_xas import read_from_input_information


def test_input_information(filename_cu_from_pymca):
    """Test providing urls to spec files"""
    input_information = InputInformation(
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca, col_name="Column 1"
        ),
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca, col_name="Column 2"
        ),
    )
    xas_obj = read_from_input_information(input_information)
    assert xas_obj.energy is not None
    assert xas_obj.spectra.data.flat[0] is not None


def test_input_information_monitor(filename_cu_from_pymca):
    """Test monitor division"""
    input_information = InputInformation(
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca, col_name="Column 1"
        ),
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca, col_name="Column 2"
        ),
        mu_ref_url=build_ascii_data_url(
            file_path=filename_cu_from_pymca, col_name="Column 2"
        ),
    )
    xas_obj = read_from_input_information(input_information)
    numpy.testing.assert_allclose(xas_obj.spectra.data[0, 0].mu, 1)


def test_input_information_minlog(filename_cu_from_larch):
    """Test minus logarithm"""

    # Note: in the data we are using, the mu column is already divided byt i0
    #       but it does not matter for this test, we just need three columns.

    # Read -log(mu/i0)
    input_information = InputInformation(
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="energy"
        ),
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="mu"
        ),
        mu_ref_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="i0"
        ),
        min_log=True,
    )
    xas_obj = read_from_input_information(input_information)
    corr_mu = xas_obj.spectra.data[0, 0].mu

    # Read mu
    input_information = InputInformation(
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="energy"
        ),
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="mu"
        ),
    )
    xas_obj = read_from_input_information(input_information)
    mu = xas_obj.spectra.data[0, 0].mu

    # Read i0
    input_information = InputInformation(
        channel_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="energy"
        ),
        spectra_url=build_ascii_data_url(
            file_path=filename_cu_from_larch, col_name="i0"
        ),
    )
    xas_obj = read_from_input_information(input_information)
    i0 = xas_obj.spectra.data[0, 0].mu

    # Check that corr_mu is indeed -log(mu/i0)
    with numpy.errstate(divide="ignore", invalid="ignore"):
        expected = -numpy.log(mu / i0)
    expected[~numpy.isfinite(expected)] = 0

    numpy.testing.assert_allclose(corr_mu, expected, 1)


def test_spec_url():
    """simple test of the spec url function class"""
    file_path = "test.dat"
    scan_title = "1.1"
    col_name = "energy"
    data_slice = None
    url = build_ascii_data_url(
        file_path=file_path,
        scan_title=scan_title,
        col_name=col_name,
        data_slice=data_slice,
    )
    assert isinstance(url, DataUrl)
    expected = ("ascii", file_path, scan_title, col_name, data_slice)
    assert split_ascii_url(url) == expected


def test_input_information_from_h5(hdf5_filename_cu_from_pymca):
    energy_url = DataUrl(
        f"silx://{hdf5_filename_cu_from_pymca}::/1.1/measurement/energy"
    )
    with h5py_utils.open_item(energy_url.file_path(), energy_url.data_path()) as dset:
        energy = dset[()]

    mu_url = DataUrl(f"silx://{hdf5_filename_cu_from_pymca}::/1.1/measurement/mu")
    with h5py_utils.open_item(mu_url.file_path(), mu_url.data_path()) as dset:
        mu = dset[()]

    input_information = InputInformation(channel_url=energy_url, spectra_url=mu_url)
    xas_obj = read_from_input_information(input_information)

    sp = xas_obj.get_spectrum(0, 0)
    numpy.testing.assert_allclose(sp.energy, energy)
    numpy.testing.assert_allclose(sp.mu, mu)


def test_input_information_from_h5_ref_url(hdf5_filename_cu_from_pymca):
    energy_url = DataUrl(
        f"silx://{hdf5_filename_cu_from_pymca}::/1.1/measurement/energy"
    )
    with h5py_utils.open_item(energy_url.file_path(), energy_url.data_path()) as dset:
        energy = dset[()]

    it_url = DataUrl(f"silx://{hdf5_filename_cu_from_pymca}::/1.1/measurement/it")
    with h5py_utils.open_item(it_url.file_path(), it_url.data_path()) as dset:
        it = dset[()]

    i0_url = DataUrl(f"silx://{hdf5_filename_cu_from_pymca}::/1.1/measurement/i0")
    with h5py_utils.open_item(i0_url.file_path(), i0_url.data_path()) as dset:
        i0 = dset[()]

    input_information = InputInformation(
        channel_url=energy_url, spectra_url=it_url, mu_ref_url=i0_url
    )
    xas_obj = read_from_input_information(input_information)

    sp = xas_obj.get_spectrum(0, 0)
    numpy.testing.assert_allclose(sp.energy, energy)
    numpy.testing.assert_allclose(sp.mu, it / i0)
