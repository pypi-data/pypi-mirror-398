# import json
import h5py
import numpy
import pytest
import silx.io.utils
from silx.io.url import DataUrl

from ..core.io.read_xas import read_from_url
from ..core.types.dimensions import transform_to_standard
from ..core.types.spectrum import Spectrum
from ..core.types.xasobject import XASObject
from ..core.units import ur
from ..tests.data import example_spectra


def test_from_dat(spectrum_cu_from_pymca):
    """check that we can create a Spectrum from a pymca .dat file"""
    assert spectrum_cu_from_pymca.energy is not None
    assert spectrum_cu_from_pymca.mu is not None


def test_from_numpy_array():
    """check that we can create a Spectrum from numpy arrays"""
    energy = numpy.arange(10, 20)
    mu = numpy.arange(10)
    spectrum = Spectrum(energy=energy, mu=mu)
    numpy.testing.assert_array_equal(spectrum.energy, (energy * ur.eV).m)
    numpy.testing.assert_array_equal(spectrum.mu, mu)
    mu_2 = numpy.arange(30, 40)
    spectrum.mu = mu_2
    numpy.testing.assert_array_equal(spectrum.mu, mu_2)


def test_create_from_single_spectrum(spectrum_cu_from_pymca):
    """check that we can create a XASObject from a pymca .dat file"""
    configuration = {
        "FT": {"KWeight": 1},
        "EXAFS": {"EXAFSNormalized": numpy.array([1, 2, 3])},
    }
    obj = XASObject(
        spectra=(spectrum_cu_from_pymca,),
        energy=spectrum_cu_from_pymca.energy,
        configuration=configuration,
        dim1=1,
        dim2=1,
    )
    assert obj.n_spectrum == 1
    ddict = obj.to_dict()
    obj2 = XASObject.from_dict(ddict)
    assert obj2 == obj
    # ensure the XASObject is serializable
    # import json
    # json.dumps(obj2.to_dict())


def test_create_from_several_spectrums(tmpdir):
    """check that we can create a XASObject from numpy arrays"""
    energy, spectra = example_spectra(shape=(256, 20, 10))
    spectra_path = "/data/NXdata/data"
    energy_path = "/data/NXdata/energy"
    filename = str(tmpdir / "myfile.h5")
    with h5py.File(filename, "a") as f:
        f[spectra_path] = spectra
        f[energy_path] = energy

    xas_obj = read_from_url(
        spectra_url=DataUrl(file_path=filename, data_path=spectra_path, scheme="silx"),
        channel_url=DataUrl(file_path=filename, data_path=energy_path, scheme="silx"),
        dimensions=(2, 1, 0),
    )
    assert xas_obj.spectra.shape[0] == 20
    assert xas_obj.spectra.shape[1] == 10
    assert xas_obj.n_spectrum == 20 * 10
    ddict = xas_obj.to_dict()
    original_spectra = silx.io.utils.get_data(
        DataUrl(file_path=filename, data_path=spectra_path, scheme="silx")
    )
    obj2 = XASObject.from_dict(ddict)
    assert xas_obj.n_spectrum == obj2.n_spectrum
    obj2_mu_spectra = obj2.spectra.as_ndarray("mu")

    numpy.testing.assert_array_equal(original_spectra, obj2_mu_spectra)
    assert obj2 == xas_obj


@pytest.fixture()
def serialize_data(tmpdir):
    energy, spectra = example_spectra(shape=(256, 20, 10))
    spectra_path = "/data/NXdata/data"
    energy_path = "/data/NXdata/energy"
    filename = str(tmpdir / "myfile.h5")
    with h5py.File(filename, "a") as f:
        f[spectra_path] = spectra
        f[energy_path] = energy
    return energy, spectra, filename


def test_transform_to_standard():
    """Test dimension transformations"""
    data = numpy.empty((4, 5, 6))
    shape = transform_to_standard(data, None).shape
    assert shape == (4, 5, 6)
    shape = transform_to_standard(data, (2, 1, 0)).shape
    assert shape == (4, 5, 6)
    shape = transform_to_standard(data, (0, 1, 2)).shape
    assert shape == (6, 5, 4)
    shape = transform_to_standard(data, (1, 2, 0)).shape
    assert shape == (5, 4, 6)
    shape = transform_to_standard(data, (0, 2, 1)).shape
    assert shape == (6, 4, 5)
    shape = transform_to_standard(data, (2, 0, 1)).shape
    assert shape == (4, 6, 5)
    shape = transform_to_standard(data, (1, 0, 2)).shape
    assert shape == (5, 6, 4)
