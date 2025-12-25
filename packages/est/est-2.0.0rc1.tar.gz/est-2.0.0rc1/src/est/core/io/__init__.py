"""
est input / output module
"""

import warnings

_DEPRECATED_MAP = {
    "read_from_url": "est.core.io.read_from_url is deprecated. Import directly from est.core.io.read_xas.read_from_url instead.",
    "read_from_ascii": "est.core.io.read_from_ascii is deprecated. Import directly from est.core.io.read_xas.read_from_ascii instead.",
    "read_from_input_information": "est.core.io.read_from_input_information is deprecated. Import directly from est.core.io.read_xas.read_from_input_information instead.",
    "dump_xas": "est.core.io.dump_xas is deprecated. Import directly from est.core.io.write_xas.write_xas instead.",
}


def __getattr__(name: str):
    if name in _DEPRECATED_MAP:
        warnings.warn(
            _DEPRECATED_MAP[name],
            DeprecationWarning,
            stacklevel=2,
        )
        # Lazy import of the attribute
        if name == "read_from_url":
            from .read_xas import read_from_url

            return read_from_url
        elif name == "read_from_ascii":
            from .read_xas import read_from_ascii

            return read_from_ascii
        elif name == "read_from_input_information":
            from .read_xas import read_from_input_information

            return read_from_input_information
        elif name == "dump_xas":
            from .write_xas import write_xas as dump_xas

            return dump_xas
    raise AttributeError(f"module {__name__} has no attribute {name}")
