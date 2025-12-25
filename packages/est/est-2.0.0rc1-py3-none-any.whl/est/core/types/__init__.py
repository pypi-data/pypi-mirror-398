"""
est.core.types module: contains main core level est types
"""

import warnings

_DEPRECATED_MAP = {
    "Sample": "est.core.types.Sample is deprecated. Import directly from est.types.sample instead.",
    "Spectra": "est.core.types.Spectra is deprecated. Import directly from est.types.spectra instead.",
    "Spectrum": "est.core.types.Spectrum is deprecated. Import directly from est.types.spectrum instead.",
    "XASObject": "est.core.types.XASObject is deprecated. Import directly from est.types.xasobject instead.",
}


def __getattr__(name: str):
    if name in _DEPRECATED_MAP:
        warnings.warn(_DEPRECATED_MAP[name], DeprecationWarning, stacklevel=2)
        # Dynamically import and return the object
        if name == "Sample":
            from .sample import Sample

            return Sample
        elif name == "Spectra":
            from .spectra import Spectra

            return Spectra
        elif name == "Spectrum":
            from .spectrum import Spectrum

            return Spectrum
        elif name == "XASObject":
            from .xasobject import XASObject

            return XASObject
    raise AttributeError(f"module {__name__} has no attribute {name}")
