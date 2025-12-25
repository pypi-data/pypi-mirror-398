"""wrapper to the larch pre-edge process"""

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
from larch.xafs.pre_edge import pre_edge

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process
from ..handle_nan import array_undo_mask

_logger = logging.getLogger(__name__)


def process_spectr_pre_edge(
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
    _logger.debug("start pre_edge on spectrum (%s, %s)", spectrum.x, spectrum.y)

    spectrum.e0 = configuration.get("e0", None) or spectrum.e0

    pre_edge_kwargs = {}
    for config_key in (
        "z",
        "edge",
        "pre1",
        "pre2",
        "norm1",
        "nnorm",
        "nvict",
        "step",
        "make_flat",
        "norm2",
        "order",
        "leexiang",
        "tables",
        "fit_erfc",
    ):
        if config_key in configuration:
            pre_edge_kwargs[config_key] = configuration[config_key]

    res_group = Group()
    mask = numpy.isfinite(spectrum.mu)

    try:
        pre_edge(
            energy=spectrum.energy[mask],
            mu=spectrum.mu[mask],
            group=res_group,
            e0=spectrum.e0,
            **pre_edge_kwargs,
        )
        failed = False
    except ValueError as e:
        if sum(mask) >= 20:
            raise
        _logger.warning(
            "Larch pre_edge failed (%s). Less than 20 valid data points so return empty result.",
            e,
        )
        mask = numpy.array([])
        res_group.norm = numpy.array([])
        res_group.flat = numpy.array([])
        res_group.pre_edge = numpy.array([])
        res_group.post_edge = numpy.array([])
        res_group.e0 = spectrum.e0
        res_group.edge_step = numpy.nan
        failed = True

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)

    if failed:
        # Dimensions of spectrum.normalized_mu and spectrum.energy must correspond.
        # So spectrum.mu must follow as well.
        spectrum.energy = numpy.array([])
        spectrum.mu = numpy.array([])

    spectrum.normalized_mu = array_undo_mask(res_group.norm, mask)
    spectrum.flatten_mu = array_undo_mask(res_group.flat, mask)
    spectrum.e0 = res_group.e0
    spectrum.pre_edge = res_group.pre_edge
    spectrum.post_edge = res_group.post_edge
    spectrum.edge_step = res_group.edge_step

    if callbacks:
        for callback in callbacks:
            callback()

    return configuration, spectrum


def larch_pre_edge(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = Larch_pre_edge(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class Larch_pre_edge(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["pre_edge_config"],
    output_names=["xas_obj"],
):
    """Pre- and post-edge normalization of XAS spectra."""

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        pre_edge_config = self.get_input_value("pre_edge_config", dict())
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_spectr_pre_edge(
                spectrum=spectrum,
                configuration=pre_edge_config,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "pre_edge calculation"

    def program_version(self) -> str:
        return get_version("larch")

    @staticmethod
    def program_name() -> str:
        return "larch_pre_edge"
