from typing import Generator

import numpy
import pytest
from ewoksorange.tests.conftest import ewoks_orange_canvas  # noqa F401
from ewoksorange.tests.conftest import qtapp  # noqa F401
from ewoksorange.tests.conftest import raw_ewoks_orange_canvas  # noqa F401

from .. import resources
from ..core.types.spectrum import Spectrum
from . import data


@pytest.fixture()
def example_pymca() -> Generator[str, None, None]:
    with resources.tutorial_workflow("example_pymca.ows") as path:
        yield str(path)


@pytest.fixture()
def example_larch() -> Generator[str, None, None]:
    with resources.tutorial_workflow("example_larch.ows") as path:
        yield str(path)


@pytest.fixture()
def example_bm23() -> Generator[str, None, None]:
    with resources.tutorial_workflow("example_bm23.ows") as path:
        yield str(path)


@pytest.fixture()
def filename_cu_from_pymca() -> Generator[str, None, None]:
    with resources.resource_path("exafs", "EXAFS_Cu.dat") as path:
        yield str(path)


@pytest.fixture()
def filename_cu_from_larch() -> Generator[str, None, None]:
    with resources.resource_path("exafs", "cu_rt01.xmu") as path:
        yield str(path)


@pytest.fixture()
def spectrum_cu_from_pymca() -> Spectrum:
    energy, mu = data.example_spectrum("exafs", "EXAFS_Cu.dat")
    return Spectrum(energy=energy, mu=mu)


@pytest.fixture()
def spectrum_cu_from_larch() -> Spectrum:
    energy, mu = data.example_spectrum("exafs", "cu_rt01.xmu")
    return Spectrum(energy=energy, mu=mu)


@pytest.fixture()
def limited_data_spectrum() -> Spectrum:
    return Spectrum(energy=numpy.array([7.1]), mu=numpy.array([1.1]))


@pytest.fixture()
def hdf5_filename_cu_from_pymca(tmpdir) -> str:
    return str(
        resources.generate_resource(
            "exafs", "EXAFS_Cu.dat", word="L", output_directory=str(tmpdir)
        )
    )
