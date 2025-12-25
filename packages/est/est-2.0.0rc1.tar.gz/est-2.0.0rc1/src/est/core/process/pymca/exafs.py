"""wrapper to pymca `exafs` process"""

import logging
from importlib.metadata import version as get_version
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union

from PyMca5.PyMcaPhysics.xas.XASClass import XASClass
from PyMca5.PyMcaPhysics.xas.XASClass import e2k

from ...types.spectrum import Spectrum
from ...types.xasobject import XASObject
from ..base import Process

_logger = logging.getLogger(__name__)


def process_spectr_exafs(
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
    _logger.debug("start exafs on spectrum (%s, %s)", spectrum.x, spectrum.y)

    pymca_xas = XASClass()
    pymca_xas.setSpectrum(energy=spectrum.energy, mu=spectrum.mu)
    if configuration is not None:
        pymca_xas.setConfiguration(configuration)

    if spectrum.pre_edge is None:
        raise ValueError("No pre-edge computing yet. Please call normalization first")

    e0 = pymca_xas.calculateE0()
    chi = pymca_xas._mu - spectrum.pre_edge
    k = e2k(pymca_xas._energy - e0)
    results = pymca_xas.postEdge(k, chi)

    exafs = (chi - results["PostEdgeB"]) / results["PostEdgeB"]
    if results["KWeight"]:
        exafs *= pow(k, results["KWeight"])

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.k = k
    spectrum.chi = chi
    spectrum.pymca_dict.PostEdgeK = results["PostEdgeK"]
    spectrum.pymca_dict.PostEdgeB = results["PostEdgeB"]
    spectrum.pymca_dict.KMin = results["KMin"]
    spectrum.pymca_dict.KMax = results["KMax"]
    spectrum.pymca_dict.KnotsX = results["KnotsX"]
    spectrum.pymca_dict.KnotsY = results["KnotsY"]
    spectrum.pymca_dict.KWeight = results["KWeight"]
    spectrum.pymca_dict.EXAFSNormalized = exafs

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


def pymca_exafs(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = PyMca_exafs(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class PyMca_exafs(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["exafs"],
    output_names=["xas_obj"],
):
    """Extract the fine-structure from XAS spectra."""

    def set_properties(self, properties):
        if "_pymcaSettings" in properties:
            self.setConfiguration(properties["_pymcaSettings"])

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        if self.inputs.exafs:
            self.setConfiguration(self.inputs.exafs)
            xas_obj.configuration["EXAFS"] = self.inputs.exafs

        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        self._advancement.endProcess()
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra.data.flat):
            assert (
                spectrum.pre_edge is not None
            ), "normalization has not been properly executed"
            process_spectr_exafs(
                spectrum=spectrum,
                configuration=xas_obj.configuration,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "exafs calculation"

    def program_version(self) -> str:
        return get_version("PyMca5")

    @staticmethod
    def program_name() -> str:
        return "pymca_exafs"
