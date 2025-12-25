"""wrapper to the larch autobk process"""

import logging
import warnings
from importlib.metadata import version as get_version
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union

import numpy
from larch.symboltable import Group
from larch.xafs.autobk import autobk
from larch.xafs.rebin_xafs import rebin_xafs

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process

_logger = logging.getLogger(__name__)


def process_spectr_autobk(
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
    :return: processed spectrum
    """
    _logger.debug("start autobk on spectrum (%s, %s)", spectrum.x, spectrum.y)

    spectrum.edge_step = configuration.get("edge_step", None) or spectrum.edge_step
    spectrum.e0 = configuration.get("e0", None) or spectrum.e0

    autobk_kwargs = {}
    for config_key in (
        "rbkg",
        "nknots",
        "kmin",
        "kmax",
        "kweight",
        "dk",
        "win",
        "k_std",
        "chi_std",
        "nfft",
        "kstep",
        "pre_edge_kws",
        "nclamp",
        "clamp_lo",
        "clamp_hi",
        "calc_uncertainties",
        "err_sigma",
    ):
        if config_key in configuration:
            autobk_kwargs[config_key] = configuration[config_key]

    mask = numpy.isfinite(spectrum.mu)
    if spectrum.e0 is None:
        if sum(mask) >= 2:
            spectrum.e0 = _max_first_derivative(
                spectrum.energy[mask], spectrum.mu[mask]
            )
        else:
            spectrum.e0 = numpy.nan

    rebin_group = Group()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            rebin_xafs(
                energy=spectrum.energy[mask],
                mu=spectrum.mu[mask],
                e0=spectrum.e0,
                group=rebin_group,
                method="boxcar",
            )
        except ValueError as e:
            if sum(mask) >= 10:
                raise
            _logger.warning(
                "Larch rebin_xafs failed (%s). Less than 10 valid data points so skip.",
                e,
            )
            rebin_group.rebinned = Group()
            rebin_group.rebinned.energy = numpy.array([])
            rebin_group.rebinned.mu = numpy.array([])

    autobk_group = Group()
    try:
        autobk(
            energy=rebin_group.rebinned.energy,
            mu=rebin_group.rebinned.mu,
            group=autobk_group,
            edge_step=spectrum.edge_step,
            ek0=spectrum.e0,
            **autobk_kwargs,
        )
    except ValueError as e:
        if sum(mask) >= 10:
            raise
        _logger.warning(
            "Larch autobk failed (%s). Less than 10 valid data points so return empty result.",
            e,
        )
        autobk_group.chi = numpy.array([])
        autobk_group.k = numpy.array([])
        autobk_group.bkg = numpy.array([])
        autobk_group.ek0 = numpy.nan

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.chi = autobk_group.chi
    spectrum.k = autobk_group.k
    spectrum.e0 = autobk_group.ek0
    spectrum.larch_dict.bkg = autobk_group.bkg

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


def _max_first_derivative(x: numpy.ndarray, y: numpy.ndarray) -> Optional[float]:
    if x.size == 0:
        return
    dy_dx = numpy.gradient(y, x)
    max_derivative_index = numpy.argmax(dy_dx)
    return x[max_derivative_index]


def larch_autobk(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = Larch_autobk(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class Larch_autobk(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["autobk_config"],
    output_names=["xas_obj"],
):
    """Extract the fine-structure from XAS spectra by subtracting
    the "background" (the jump without oscillations).
    """

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        self.progress = 0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        autobk_config = self.get_input_value("autobk_config", dict())
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_spectr_autobk(
                spectrum=spectrum,
                configuration=autobk_config,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "autobk calculation"

    def program_version(self) -> str:
        return get_version("larch")

    @staticmethod
    def program_name() -> str:
        return "larch_autobk"
