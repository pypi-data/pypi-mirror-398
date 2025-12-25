import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Sequence

import numpy
import scipy.signal

from ..types.spectrum import Spectrum
from ..types.xasobject import XASObject
from .base import Process
from .handle_nan import array_undo_mask

_logger = logging.getLogger(__name__)


def process_noise_savgol(
    spectrum: Spectrum,
    configuration: Dict[str, Any],
    overwrite: bool = True,
    callbacks: Optional[Sequence[Callable[[], None]]] = None,
) -> Spectrum:
    """
    :param spectrum: spectrum to process.
    :param configuration: configuration of the pymca normalization.
    :param overwrite: `False` if we want to return a new Spectrum instance.
    :param callbacks: callbacks to execute after processing.
    :return: processed spectrum.
    """
    _logger.debug(
        "start noise with Savitsky-Golay on spectrum (%s, %s)", spectrum.x, spectrum.y
    )
    if "noise" in configuration:
        configuration = configuration["noise"]
    if "window_size" not in configuration:
        raise ValueError("`window_size` should be specify. Missing in configuration")
    else:
        window_size = configuration["window_size"]
    if "polynomial_order" not in configuration:
        raise ValueError(
            "`polynomial_order` should be specify. Missing in configuration"
        )
    else:
        polynomial_order = configuration["polynomial_order"]
    if spectrum.e0 is None:
        raise ValueError(
            "e0 is None. Unable to compute noise. (e0 is determine in pre_edge. You must run it first)"
        )

    mask = numpy.isfinite(spectrum.mu)

    # compute noise. This is always done over the full spectrum
    # get e_min and e_max. Those will be
    try:
        smooth_spectrum = scipy.signal.savgol_filter(
            spectrum.mu[mask], window_size, polynomial_order
        )
    except ValueError as e:
        if sum(mask) >= 10:
            raise
        _logger.warning(
            "savgol_filter failed (%s). Less than 10 valid data points so return empty result.",
            e,
        )
        mask = numpy.array([])
        smooth_spectrum = numpy.array([])

    smooth_spectrum = array_undo_mask(smooth_spectrum, mask)
    noise = numpy.absolute(spectrum.mu - smooth_spectrum)

    # compute e_min and e_max. those are provided relative to the edge
    e_min = configuration.get("e_min", None)
    e_max = configuration.get("e_max", None)

    if e_min is None:
        if spectrum.energy.size == 0:
            e_min = numpy.nan
        else:
            e_min = spectrum.energy.min()
    else:
        e_min += spectrum.e0
    if e_max is None:
        if spectrum.energy.size == 0:
            e_max = numpy.nan
        else:
            e_max = spectrum.energy.max()
    else:
        e_max += spectrum.e0

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.noise_savgol = noise
    spectrum.noise_e_min = e_min
    spectrum.noise_e_max = e_max
    if mask.size:
        mask = mask & (spectrum.energy > e_min) & (spectrum.energy < e_max)

    if mask.any():
        if spectrum.edge_step is None:
            raise ValueError(
                "edge_step is None. Unable to compute noise. (edge_step is determine in pre_edge. You must run it first)"
            )

        spectrum.raw_noise_savgol = numpy.mean(noise[mask])
        spectrum.norm_noise_savgol = spectrum.raw_noise_savgol / spectrum.edge_step
    else:
        # Uses nan's instead of raising an exception. Otherwise we have much more failing
        # workflows online (either E0 is wrong or the scan has not progressed past Emin,
        # which is after the edge so the plots are fine).
        spectrum.raw_noise_savgol = numpy.nan
        spectrum.norm_noise_savgol = numpy.nan

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


class NoiseProcess(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["window_size", "polynomial_order", "e_min", "e_max"],
    output_names=["xas_obj"],
):
    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)

        parameters = {
            "window_size": self.get_input_value("window_size", 5),
            "polynomial_order": self.get_input_value("polynomial_order", 2),
        }
        if not self.missing_inputs.e_min:
            parameters["e_min"] = self.inputs.e_min
        if not self.missing_inputs.e_max:
            parameters["e_max"] = self.inputs.e_max
        xas_obj.configuration["noise"] = parameters

        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_noise_savgol(
                spectrum=spectrum,
                configuration=xas_obj.configuration,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "noise using Savitsky-Golay algorithm"

    @staticmethod
    def program_name() -> str:
        return "noise_savgol"
