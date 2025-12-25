"""wrapper to pymca `ft` process"""

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


def process_spectr_ft(
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
    assert isinstance(spectrum, Spectrum)
    _logger.debug(
        "start fourier transform on spectrum (%s, %s)", spectrum.x, spectrum.y
    )

    if spectrum.energy is None or spectrum.mu is None:
        _logger.error("Energy and or Mu is/are not specified, unable to compute exafs")
        return None

    pymca_xas = XASClass()
    if configuration is not None:
        pymca_xas.setConfiguration(configuration)
    pymca_xas.setSpectrum(energy=spectrum.energy, mu=spectrum.mu)

    if spectrum.chi is None:
        _logger.warning(
            "exafs has not been processed yet, unable to process fourier transform"
        )
        return None

    if spectrum.pymca_dict.EXAFSNormalized is None:
        _logger.warning("ft window need to be defined first")
        return None

    ddict = pymca_xas.fourierTransform(
        spectrum.k,
        spectrum.pymca_dict.EXAFSNormalized,
        kMin=spectrum.pymca_dict.KMin,
        kMax=spectrum.pymca_dict.KMax,
    )

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    spectrum.ft.radius = ddict["FTRadius"]
    spectrum.ft.intensity = ddict["FTIntensity"]
    spectrum.ft.real = ddict["FTReal"]
    spectrum.ft.imaginary = ddict["FTImaginary"]

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


def pymca_ft(xas_obj: Union[XASObject, dict], **optional_inputs) -> Optional[XASObject]:
    process = PyMca_ft(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class PyMca_ft(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["ft"],
    output_names=["xas_obj"],
):
    """Fourier transform of the XAS fine-structure."""

    def set_properties(self, properties):
        if "_pymcaSettings" in properties:
            self._settings = properties["_pymcaSettings"]

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)

        if self.inputs.ft:
            self.setConfiguration(self.inputs.ft)
            xas_obj.configuration["FT"] = self.inputs.ft

        self._advancement.reset(max_=xas_obj.n_spectrum)
        self._advancement.startProcess()
        self._pool_process(xas_obj=xas_obj)
        self._advancement.endProcess()
        assert hasattr(xas_obj.spectra.data.flat[0], "ft")
        assert hasattr(xas_obj.spectra.data.flat[0].ft, "intensity")
        assert hasattr(xas_obj.spectra.data.flat[0].ft, "imaginary")
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra):
            process_spectr_ft(
                spectrum=spectrum,
                configuration=xas_obj.configuration,
                callbacks=self.callbacks,
                overwrite=True,
            )
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "fourier transform"

    def program_version(self) -> str:
        return get_version("PyMca5")

    @staticmethod
    def program_name() -> str:
        return "pymca_ft"
