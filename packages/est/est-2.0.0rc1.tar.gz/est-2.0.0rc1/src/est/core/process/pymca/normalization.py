"""wrapper to pymca `normalization` process"""

import logging
from importlib.metadata import version as get_version
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union

from PyMca5.PyMcaPhysics.xas.XASClass import XASClass

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process

_logger = logging.getLogger(__name__)


def process_spectr_norm(
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
    _logger.debug("start normalization on spectrum (%s, %s)", spectrum.x, spectrum.y)

    pymca_xas = XASClass()
    pymca_xas.setSpectrum(energy=spectrum.energy, mu=spectrum.mu)
    if configuration is not None:
        if "e0" in configuration:
            configuration["E0Value"] = configuration["e0"]
            configuration["E0Method"] = "Manual"
        pymca_xas.setConfiguration(configuration)
    res = pymca_xas.normalize()

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.normalized_energy = res.get("NormalizedEnergy", None)
    spectrum.normalized_mu = res.get("NormalizedMu", None)
    spectrum.e0 = res.get("Edge", None)
    spectrum.pre_edge = res.get("NormalizedBackground", None)
    spectrum.post_edge = res.get("NormalizedSignal", None)

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


def pymca_normalization(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = PyMca_normalization(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class PyMca_normalization(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["normalization"],
    output_names=["xas_obj"],
):
    """Pre- and post-edge normalization of XAS spectra."""

    def set_properties(self, properties):
        if "_pymcaSettings" in properties:
            self._settings = properties["_pymcaSettings"]

    def run(self):
        xas_obj = self.getXasObject(self.inputs.xas_obj)

        if xas_obj.energy is None:
            _logger.error("Energy not specified, unable to normalize spectra")
            return

        if self.inputs.normalization:
            self.setConfiguration(self.inputs.normalization)
            xas_obj.configuration["Normalization"] = self.inputs.normalization

        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        if xas_obj.normalized_energy is None:
            raise ValueError("Fail to compute normalize energy")

        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra.data.flat):
            process_spectr_norm(
                spectrum=spectrum,
                configuration=xas_obj.configuration,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "Normalization of the spectrum"

    def program_version(self) -> str:
        return get_version("PyMca5")

    @staticmethod
    def program_name() -> str:
        return "pymca_normalization"
