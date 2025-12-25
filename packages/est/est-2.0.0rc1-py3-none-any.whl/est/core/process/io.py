import warnings

from .read import ReadXasObject as _ReadXasObject
from .write import WriteXasObject as _WriteXasObject


class ReadXasObject(_ReadXasObject):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "est.process.io.ReadXasObject is deprecated and will be removed in a future release. "
            "Use est.process.read.ReadXasObject instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class DumpXasObject(_WriteXasObject):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "est.process.io.DumpXasObject is deprecated and will be removed in a future release. "
            "Use est.process.write.WriteXasObject instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
