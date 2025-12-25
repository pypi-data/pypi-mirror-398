# import json
import h5py
import numpy
import pytest
from silx.io.url import DataUrl
from silx.io.utils import get_data

from ..core.io.read_xas import read_from_url
from ..core.types.xasobject import XASObject
from .data import example_spectra


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
    print("#############################")
    obj2 = XASObject.from_dict(ddict)
    assert obj2 == obj
    # ensure the XASObject is serializable
    # import json
    # json.dumps(obj2.to_dict())


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


def test_create_from_several_spectrums(serialize_data):
    """check that we can create a XASObject from numpy arrays"""
    _, _, filename = serialize_data

    xas_obj = read_from_url(
        spectra_url=DataUrl(
            file_path=filename, data_path="/data/NXdata/data", scheme="silx"
        ),
        channel_url=DataUrl(
            file_path=filename, data_path="/data/NXdata/energy", scheme="silx"
        ),
        dimensions=(2, 1, 0),
    )
    assert xas_obj.spectra.shape[0] == 20
    assert xas_obj.spectra.shape[1] == 10
    assert xas_obj.n_spectrum == 20 * 10
    ddict = xas_obj.to_dict()
    original_spectra = get_data(
        DataUrl(file_path=filename, data_path="/data/NXdata/data", scheme="silx")
    )
    obj2 = XASObject.from_dict(ddict)
    assert xas_obj.n_spectrum == obj2.n_spectrum
    obj2_mu_spectra = obj2.spectra.as_ndarray("mu")

    numpy.testing.assert_array_equal(original_spectra, obj2_mu_spectra)
    assert obj2 == xas_obj
