"""wrapper to the larch xftf process"""

import logging
from importlib.metadata import version as get_version
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union

import numpy
from larch.symboltable import Group
from larch.xafs.xafsft import xftf

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process

_logger = logging.getLogger(__name__)


def process_spectr_xftf(
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
    _logger.debug("start xftf on spectrum (%s, %s)", spectrum.x, spectrum.y)

    # if kmax is not provided take default value
    kmax = configuration.get("kmax", None)
    if kmax is None:
        if spectrum.k.size:
            configuration["kmax"] = max(spectrum.k) * 0.9
        else:
            configuration["kmax"] = numpy.nan
    kmin = configuration.get("kmin", None)
    if kmin is None:
        if spectrum.k.size:
            configuration["kmin"] = min(spectrum.k)
        else:
            configuration["kmin"] = numpy.nan

    xftf_kwargs = {}
    for config_key in (
        "kmin",
        "kmax",
        "kweight",
        "dk",
        "dk2",
        "with_phase",
        "window",
        "rmax_out",
        "nfft",
        "kstep",
    ):
        if config_key in configuration:
            xftf_kwargs[config_key] = configuration[config_key]
            if config_key == "kweight":
                xftf_kwargs["kw"] = configuration[config_key]

    res_group = Group()
    mask = numpy.isfinite(spectrum.chi)
    with_phase = xftf_kwargs.get("with_phase", False)

    try:
        xftf(k=spectrum.k[mask], chi=spectrum.chi[mask], group=res_group, **xftf_kwargs)
    except (ValueError, IndexError) as e:
        if sum(mask) >= 10:
            raise
        _logger.warning(
            "Larch xftf failed (%s). Less than 10 valid data points so return empty result.",
            e,
        )
        res_group.r = numpy.array([])
        res_group.chir = numpy.array([])
        res_group.chir_mag = numpy.array([])
        res_group.chir_re = numpy.array([])
        res_group.chir_im = numpy.array([])
        if with_phase:
            res_group.chir_pha = numpy.array([])

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.ft.radius = res_group.r
    spectrum.ft.intensity = res_group.chir_mag
    spectrum.ft.real = res_group.chir_re
    spectrum.ft.imaginary = res_group.chir_im

    if with_phase:
        spectrum.ft.phase = res_group.chir_pha
    else:
        spectrum.ft.phase = None

    # handle chi(x) * k**k_weight plot with r max
    if spectrum.k is not None and spectrum.chi is not None:
        if "kweight" in xftf_kwargs:
            kweight = xftf_kwargs["kweight"]
        else:
            kweight = 0

    spectrum.chi_weighted_k = spectrum.chi * (spectrum.k**kweight)
    spectrum.larch_dict.xftf_k_weight = kweight
    spectrum.larch_dict.xftf_k_min = configuration["kmin"]
    spectrum.larch_dict.xftf_k_max = configuration["kmax"]

    if callbacks:
        for callback in callbacks:
            callback()

    return configuration, spectrum


def larch_xftf(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = Larch_xftf(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class Larch_xftf(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["xftf_config"],
    output_names=["xas_obj"],
):
    """Fourier transform of the XAS fine-structure."""

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        self._advancement.reset(max_=xas_obj.n_spectrum)
        self._advancement.startProcess()
        self._pool_process(xas_obj=xas_obj)
        self._advancement.endProcess()
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj):
        xftf_config = self.get_input_value("xftf_config", dict())
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_spectr_xftf(
                spectrum=spectrum,
                configuration=xftf_config,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "xftf calculation"

    def program_version(self) -> str:
        return get_version("larch")

    @staticmethod
    def program_name() -> str:
        return "larch_xftf"
