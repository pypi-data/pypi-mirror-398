from typing import Tuple

import numpy
from numpy.typing import ArrayLike

from ..resources import resource_path


def example_spectrum(*args) -> Tuple[ArrayLike, ArrayLike]:
    if not args:
        args = "exafs", "EXAFS_Ge.dat"
    if isinstance(args[0], str):
        with resource_path(*args) as path:
            energy, mu, *_ = numpy.loadtxt(path).T
    else:
        energy = numpy.linspace(*args)  # eV
        mi, ma = energy.min(), energy.max()
        edge = mi + (ma - mi) * 0.08
        mu = numpy.linspace(0.6, 0.1, energy.size) + (energy > edge).astype(int)
    return energy, mu


def example_spectra(
    *args,
    shape: Tuple[int] = (0, 1, 1),
    noise: bool = False,
) -> Tuple[ArrayLike, ArrayLike]:
    """Replicate a single spectrum to a nD dataset with optional noise addition."""
    energy, mu = example_spectrum(*args)
    nenergy = shape[0]
    if shape[0]:
        assert nenergy <= len(energy)
        energy = energy[:nenergy]
        mu = mu[:nenergy]
    else:
        nenergy = len(energy)
    mu = mu.reshape((nenergy,) + (1,) * (len(shape) - 1))
    tile_repts = (1,) + shape[1:]
    mu = numpy.tile(mu, tile_repts)
    if noise:
        mu += numpy.random.normal(0.0, 0.05, shape)
    return energy, mu
