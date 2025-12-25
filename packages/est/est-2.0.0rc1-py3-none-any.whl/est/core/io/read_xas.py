import logging
from typing import Optional
from typing import Tuple

import numpy
import pint
from silx.io.url import DataUrl

from ... import settings
from ..monotonic import split_piecewise_monotonic
from ..sections import split_section_size
from ..types.dimensions import DimensionsType
from ..types.dimensions import transform_to_standard
from ..types.xasobject import XASObject
from ..units import ur
from ._utils.ascii import build_ascii_data_url
from ._utils.load import load_data
from ._utils.parse import parse_energy_mu
from .information import InputInformation

_logger = logging.getLogger(__name__)


def read_from_input_information(
    information: InputInformation, timeout: float = settings.DEFAULT_READ_TIMEOUT
) -> XASObject:
    energy = load_data(information.channel_url, retry_timeout=timeout)
    if isinstance(energy, pint.Quantity):
        energy = energy.m_as(information.energy_unit)

    mu = load_data(information.spectra_url, retry_timeout=timeout)
    if isinstance(mu, pint.Quantity):
        mu = mu.m_as("dimensionless")

    if information.mu_ref_url:
        monitor = load_data(information.mu_ref_url, retry_timeout=timeout)
        if isinstance(monitor, pint.Quantity):
            monitor = monitor.m_as("dimensionless")
        if monitor.size == 0:
            monitor = None
    else:
        monitor = None

    energy, mu = parse_energy_mu(
        energy,
        mu,
        monitor,
        min_log=information.min_log,
        sort_on_energy=not information.is_concatenated,
    )

    if information.is_concatenated:
        if energy.ndim > 1:
            raise ValueError(
                f"{information.channel_url!r} cannot have a rank higher than 1"
            )
        if mu.ndim > 1:
            raise ValueError(
                f"{information.spectra_url!r} cannot have a rank higher than 1"
            )

        energy, mu = _split_xas_data(
            energy,
            mu,
            concatenated_spectra_section_size=information.concatenated_spectra_section_size,
            skip_concatenated_n_spectra=information.skip_concatenated_n_spectra,
            trim_concatenated_n_points=information.trim_concatenated_n_points,
        )

    energy = energy * information.energy_unit
    mu = transform_to_standard(mu, information.dimensions)
    return XASObject(spectra=mu, energy=energy)


def read_from_url(
    spectra_url: DataUrl,
    channel_url: DataUrl,
    dimensions: Optional[DimensionsType] = None,
    energy_unit=ur.eV,
    mu_ref_url: Optional[None] = None,
    is_concatenated: bool = False,
    trim_concatenated_n_points: int = 0,
    skip_concatenated_n_spectra: int = 0,
    concatenated_spectra_section_size: int = 0,
    timeout: float = settings.DEFAULT_READ_TIMEOUT,
) -> XASObject:
    """Same as :meth:`read_from_input_information` by passing all parameter unpacked."""
    input_information = InputInformation(
        spectra_url=spectra_url,
        channel_url=channel_url,
        dimensions=dimensions,
        energy_unit=energy_unit,
        mu_ref_url=mu_ref_url,
        is_concatenated=is_concatenated,
        trim_concatenated_n_points=trim_concatenated_n_points,
        skip_concatenated_n_spectra=skip_concatenated_n_spectra,
        concatenated_spectra_section_size=concatenated_spectra_section_size,
    )
    return read_from_input_information(input_information, timeout=timeout)


def read_from_ascii(
    file_path: str,
    columns_names: dict,
    energy_unit=ur.eV,
    dimensions: Optional[DimensionsType] = None,
    scan_title: Optional[str] = None,
    timeout: float = settings.DEFAULT_READ_TIMEOUT,
) -> XASObject:
    """Same as :meth:`read_from_input_information` by for ASCII without full URL's."""
    if file_path in (None, ""):
        raise ValueError("Please supply a file path !")

    input_information = InputInformation(
        spectra_url=build_ascii_data_url(
            file_path=file_path,
            col_name=columns_names["mu"],
            scan_title=scan_title,
        ),
        channel_url=build_ascii_data_url(
            file_path=file_path,
            col_name=columns_names["energy"],
            scan_title=scan_title,
        ),
        mu_ref_url=build_ascii_data_url(
            file_path=file_path,
            col_name=columns_names["monitor"],
            scan_title=scan_title,
        ),
        energy_unit=energy_unit,
        dimensions=dimensions,
    )
    return read_from_input_information(input_information, timeout=timeout)


def _split_xas_data(
    raw_energy: numpy.ndarray,
    raw_mu: numpy.ndarray,
    concatenated_spectra_section_size: int,
    skip_concatenated_n_spectra: int,
    trim_concatenated_n_points: int,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Split spectra acquired with the energy ramping up and down, with any number of repetitions.

    When the scan is uni-directional, the ramp is always up. When the scan is bi-directional the ramp is
    alternating up and down.

    The spectra are then interpolated to produce a 3D data aray (nb_energy_pts, nb_of_ramps, 1).

    Limitations: the original spectra and energy datasets must be 1D.
    """
    if concatenated_spectra_section_size:
        ramp_slices = split_section_size(raw_energy, concatenated_spectra_section_size)
    else:
        ramp_slices = split_piecewise_monotonic(raw_energy)

    if not ramp_slices:
        if len(raw_energy) >= 10:
            raise RuntimeError("Not enough data to detect monotonic slices.")
        _logger.warning(
            "Not enough data to detect monotonic slices. Less than 10 data points so return empty result.",
        )
        ramp_slices = [slice(0, 0)]

    interpolated_energy = raw_energy[ramp_slices[0]]

    if skip_concatenated_n_spectra:
        ramp_slices = ramp_slices[skip_concatenated_n_spectra:]

    interpolated_mu = numpy.zeros(
        (len(interpolated_energy), len(ramp_slices), 1), dtype=raw_mu.dtype
    )
    for i, ramp_slice in enumerate(ramp_slices):
        raw_energy_i = raw_energy[ramp_slice]
        if raw_energy_i.size == 0:
            continue
        raw_spectrum_i = raw_mu[ramp_slice]

        if len(raw_energy_i) != len(raw_spectrum_i):
            n = min(len(raw_energy_i), len(raw_spectrum_i))
            raw_energy_i = raw_energy_i[:n]
            raw_spectrum_i = raw_spectrum_i[:n]

        if trim_concatenated_n_points:
            raw_spectrum_i[:trim_concatenated_n_points] = numpy.nan
            raw_spectrum_i[-trim_concatenated_n_points:] = numpy.nan

        interpolated_mu[:, i, 0] = numpy.interp(
            interpolated_energy,
            raw_energy_i,
            raw_spectrum_i,
            left=numpy.nan,
            right=numpy.nan,
        )

    return interpolated_energy, interpolated_mu
