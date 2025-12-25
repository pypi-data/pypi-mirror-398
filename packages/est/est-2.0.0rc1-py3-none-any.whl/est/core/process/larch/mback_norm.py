"""wrapper to the larch mback-norm process"""

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
from larch.xafs.mback import mback_norm

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process
from ..handle_nan import array_undo_mask

_logger = logging.getLogger(__name__)


def process_spectr_mback_norm(
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
    _logger.debug("start mback_norm on spectrum (%s, %s)", spectrum.x, spectrum.y)
    assert isinstance(spectrum, Spectrum)
    if not hasattr(spectrum, "norm"):
        _logger.error(
            "spectrum doesn't have norm. Maybe you meed to compute "
            "pre_edge first? Unable to compute mback_norm."
        )
        return None
    if not hasattr(spectrum, "pre_edge"):
        _logger.error(
            "spectrum doesn't have pre_edge. Maybe you meed to compute "
            "pre_edge first? Unable to compute mback_norm."
        )
        return None

    mback_norm_kwargs = {}
    for config_key in (
        "z",
        "edge",
        "pre1",
        "pre2",
        "norm1",
        "norm2",
        "nnorm",
        "nvict",
    ):
        if config_key in configuration:
            mback_norm_kwargs[config_key] = configuration[config_key]
    e0 = configuration.get("e0", None) or spectrum.e0

    # Note: larch will calculate the pre-edge when missing
    res_group = Group()
    mask = numpy.isfinite(spectrum.mu)
    mback_norm(
        energy=spectrum.energy[mask],
        mu=spectrum.mu[mask],
        group=res_group,
        e0=e0,
        **mback_norm_kwargs,
    )

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.e0 = e0
    spectrum.normalized_mu = array_undo_mask(res_group.norm, mask)

    if callbacks:
        for callback in callbacks:
            callback()
    return configuration, spectrum


def larch_mback_norm(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = Larch_mback_norm(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class Larch_mback_norm(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["mback_norm_config", "mback_norm"],
    output_names=["xas_obj"],
):
    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        mback_norm_config = self.get_input_value("mback_norm_config", dict())
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_spectr_mback_norm(
                spectrum=spectrum,
                configuration=mback_norm_config,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "mback norm calculation"

    def program_version(self) -> str:
        return get_version("larch")

    @staticmethod
    def program_name() -> str:
        return "larch_mback_norm"
