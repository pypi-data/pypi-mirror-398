"""wrapper to the larch mback process"""

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
from larch.xafs.mback import mback

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process
from ..handle_nan import array_undo_mask

_logger = logging.getLogger(__name__)


def process_spectr_mback(
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
    _logger.debug("start mback on spectrum (%s, %s)", spectrum.x, spectrum.y)

    mback_kwargs = {}

    spectrum.e0 = configuration.get("e0", spectrum.e0)

    for config_key in (
        "z",
        "edge",
        "pre1",
        "pre2",
        "norm1",
        "norm2",
        "order",
        "leexiang",
        "tables",
        "fit_erfc",
    ):
        if config_key in configuration:
            mback_kwargs[config_key] = configuration[config_key]
    if "z" not in mback_kwargs:
        raise ValueError("atomic number of the absorber is not specify")

    res_group = Group()
    mask = numpy.isfinite(spectrum.mu)

    with warnings.catch_warnings():
        # Note: when lmfit>1.3.3 is released this warnings catch can be removed
        warnings.filterwarnings(
            "ignore",
            message="Using UFloat objects with std_dev==0 may give unexpected results.",
            category=UserWarning,
            module="uncertainties.core",
        )
        mback(
            spectrum.energy[mask],
            spectrum.mu[mask],
            group=res_group,
            e0=spectrum.e0,
            **mback_kwargs,
        )

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.normalized_mu = array_undo_mask(res_group.norm, mask)

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


def larch_mback(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = Larch_mback(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class Larch_mback(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["mback_config"],
    output_names=["xas_obj"],
):
    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        mback_config = self.get_input_value("mback_config", dict())
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_spectr_mback(
                spectrum=spectrum,
                configuration=mback_config,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "mback calculation"

    def program_version(self) -> str:
        return get_version("larch")

    @staticmethod
    def program_name() -> str:
        return "larch_mback"
