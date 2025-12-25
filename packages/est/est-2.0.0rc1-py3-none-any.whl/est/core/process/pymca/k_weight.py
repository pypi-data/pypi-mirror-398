"""wrapper to pymca `k-weight` process"""

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
from ..pymca.exafs import process_spectr_exafs

_logger = logging.getLogger(__name__)


def process_spectr_k(
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
        "start k weight definition on spectrum (%s, %s)", spectrum.x, spectrum.y
    )

    if spectrum.energy is None or spectrum.mu is None:
        _logger.error("Energy and or Mu is/are not specified, unable to compute exafs")
        return None

    pymca_xas = XASClass()
    pymca_xas.setSpectrum(energy=spectrum.energy, mu=spectrum.mu)
    has_kweight = configuration.get("KWeight") is not None
    if has_kweight:
        configuration["FT"]["KWeight"] = configuration["KWeight"]
        configuration["EXAFS"]["KWeight"] = configuration["KWeight"]
    pymca_xas.setConfiguration(configuration)

    # we need to update EXAFSNormalized since we are overwriting it
    exafs_res = process_spectr_exafs(spectrum=spectrum, configuration=configuration)
    if exafs_res is None:
        err = "Failed to process exafs."
        if spectrum.x is not None or spectrum.y is not None:
            err = (
                err
                + "Spectrum (x, y) coords: "
                + ",".join((str(spectrum.x), str(spectrum.y)))
            )
        raise ValueError(err)

    e0 = pymca_xas.calculateE0()
    kValues = e2k(spectrum.energy - e0)
    exafs = exafs_res.pymca_dict.EXAFSNormalized
    if has_kweight:
        exafs *= pow(kValues, configuration["KWeight"])

    if not overwrite:
        spectrum = spectrum.model_copy(deep=True)
    if has_kweight:
        spectrum.pymca_dict.KWeight = configuration["KWeight"]
    spectrum.pymca_dict.EXAFSNormalized = exafs

    if callbacks:
        for callback in callbacks:
            callback()

    return spectrum


def pymca_k_weight(
    xas_obj: Union[XASObject, dict], **optional_inputs
) -> Optional[XASObject]:
    process = PyMca_k_weight(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class PyMca_k_weight(
    Process,
    input_names=["xas_obj"],
    optional_input_names=["k_weight"],
    output_names=["xas_obj"],
):
    """K-weighting XAS spectra."""

    def set_properties(self, properties):
        if "_kWeightSetting" in properties:
            _properties = properties.copy()
            _properties["k_weight"] = _properties["_kWeightSetting"]
            del _properties["_kWeightSetting"]
            self.setConfiguration(_properties)

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)

        if self.inputs.k_weight:
            self.setConfiguration({"k_weight": self.inputs.k_weight})
            xas_obj.configuration["SET_KWEIGHT"] = self.inputs.k_weight

        if "SET_KWEIGHT" not in xas_obj.configuration:
            _logger.warning(
                "Missing configuration to know which value we should set "
                "to k weight, will be set to 0 by default"
            )
            xas_obj.configuration["SET_KWEIGHT"] = 0

        for key in ("FT", "EXAFS", "Normalization"):
            if key not in xas_obj.configuration:
                xas_obj.configuration[key] = {}

        xas_obj.configuration["KWeight"] = xas_obj.configuration["SET_KWEIGHT"]
        xas_obj.configuration["FT"]["KWeight"] = xas_obj.configuration["SET_KWEIGHT"]
        xas_obj.configuration["EXAFS"]["KWeight"] = xas_obj.configuration["SET_KWEIGHT"]
        xas_obj.configuration["Normalization"]["KWeight"] = xas_obj.configuration[
            "SET_KWEIGHT"
        ]

        self._advancement.reset(max_=xas_obj.n_spectrum)
        self.progress = 0.0
        self._pool_process(xas_obj=xas_obj)
        self.progress = 100.0
        self.outputs.xas_obj = xas_obj

    def _pool_process(self, xas_obj: XASObject):
        assert "KWeight" in xas_obj.configuration
        n_s = len(xas_obj.spectra.data.flat)
        for i_s, spectrum in enumerate(xas_obj.spectra.data.flat):
            process_spectr_k(
                spectrum=spectrum,
                configuration=xas_obj.configuration,
                callbacks=self.callbacks,
                overwrite=True,
            )
            assert "KWeight" in xas_obj.configuration
            self.progress = i_s / n_s * 100.0

    def definition(self) -> str:
        return "Define k weight for xas treatment"

    def program_version(self) -> str:
        return get_version("PyMca5")

    @staticmethod
    def program_name() -> str:
        return "pymca_k_weight"
