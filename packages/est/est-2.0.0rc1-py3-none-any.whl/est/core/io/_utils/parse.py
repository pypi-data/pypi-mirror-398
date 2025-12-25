import logging
from typing import Optional
from typing import Tuple

import numpy

_logger = logging.getLogger(__name__)


def parse_energy_mu(
    energy: Optional[numpy.ndarray],
    mu: Optional[numpy.ndarray],
    monitor: Optional[numpy.ndarray],
    min_log: bool,
    sort_on_energy: bool,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    if energy is not None and not energy.ndim == 1:
        raise ValueError("Energy is not 1D")

    if energy is None:
        energy = numpy.array([])
    if mu is None:
        mu = numpy.array([])
    has_monitor = monitor is not None

    if has_monitor:
        energy, mu, monitor = _equal_size(energy, mu, monitor)
        if sort_on_energy:
            energy, mu, monitor = _sort_on_energy(energy, mu, monitor)
    else:
        energy, mu = _equal_size(energy, mu)
        if sort_on_energy:
            energy, mu = _sort_on_energy(energy, mu)

    mu = _calculate_mu(mu, monitor, min_log)
    return energy, mu


def _sort_on_energy(
    energy: numpy.ndarray, *arrays: numpy.ndarray
) -> Tuple[numpy.ndarray]:
    strictly_increasing = numpy.diff(energy) > 0
    if strictly_increasing.all():
        return energy, *arrays
    _logger.warning("Energy is not strictly increasing: sort data by energy")
    idx = numpy.argsort(energy)
    energy = energy[idx]
    arrays = tuple(array[idx] for array in arrays)

    has_duplicates = numpy.diff(energy) == 0
    if has_duplicates.any():
        _logger.warning("Energy has duplicate values: remove duplicates")
        energy, idx = numpy.unique(energy, return_index=True)
        arrays = tuple(array[idx] for array in arrays)

    return energy, *arrays


def _equal_size(*arrays: numpy.ndarray) -> Tuple[numpy.ndarray]:
    n = set(len(arr) for arr in arrays)
    if len(n) == 1:
        return arrays
    _logger.warning("XAS data has unequal length: trim to the shortest")
    n = min(n)
    return tuple(arr[:n] for arr in arrays)


def _calculate_mu(
    numerator: numpy.ndarray, denominator: Optional[numpy.ndarray], min_log: bool
) -> numpy.ndarray:
    if denominator is None:
        mu = numerator
    else:
        with numpy.errstate(divide="ignore"):
            mu = numerator / denominator
    if min_log:
        with numpy.errstate(invalid="ignore"):
            mu = -numpy.log(mu)
    not_finite = ~numpy.isfinite(mu)
    if not_finite.any():
        _logger.warning(
            "found non-finite values after mu division by the monitor. Replace them by 0."
        )
        mu[not_finite] = 0
    return mu
