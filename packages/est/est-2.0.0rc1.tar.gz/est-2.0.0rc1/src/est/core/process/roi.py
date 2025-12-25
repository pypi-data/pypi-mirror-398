import logging
from typing import Optional
from typing import Union

from ..types.spectra import Spectra
from ..types.xasobject import XASObject
from .base import Process

_logger = logging.getLogger(__name__)


def xas_roi(xas_obj: Union[XASObject, dict], **optional_inputs) -> Optional[XASObject]:
    process = ROIProcess(inputs={"xas_obj": xas_obj, **optional_inputs})
    process.run()
    return process.get_output_value("xas_obj", None)


class _ROI:
    def __init__(self, origin, size):
        self.origin = origin
        self.size = size

    @property
    def origin(self) -> tuple:
        return self.__origin

    @origin.setter
    def origin(self, origin: Union[list, tuple]):
        self.__origin = int(origin[0]), int(origin[1])

    @property
    def size(self) -> tuple:
        return self.__size

    @size.setter
    def size(self, size: Union[list, tuple]):
        self.__size = int(size[0]), int(size[1])

    def to_dict(self) -> dict:
        return {"origin": self.origin, "size": self.size}

    @staticmethod
    def from_dict(ddict: dict):
        return _ROI(origin=ddict["origin"], size=ddict["size"])

    @staticmethod
    def from_silx_def(silx_roi):
        origin = silx_roi.getOrigin()
        size = silx_roi.getSize()
        return _ROI(origin=origin, size=size)


class ROIProcess(
    Process,
    input_names=["xas_obj", "roi_size", "roi_origin"],
    output_names=["xas_obj"],
):
    def run(self):
        if 0 in self.inputs.roi_size:
            raise ValueError(
                f"Unable to apply a roi of size 0. Requested ROI size is {self.inputs.roi_size}"
            )

        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)

        roi_size = list(self.inputs.roi_size)
        roi_origin = list(self.inputs.roi_origin)
        if roi_size[0] == -1:
            roi_origin[0] = 0
            roi_size[0] = xas_obj.spectra.shape[1]
        if roi_size[1] == -1:
            roi_origin[1] = 0
            roi_size[1] = xas_obj.spectra.shape[0]
        roi = _ROI(origin=roi_origin, size=roi_size)

        self.outputs.xas_obj = self._apply_roi(xas_obj, roi)

    def _apply_roi(self, xas_obj: XASObject, roi: _ROI):
        _logger.warning("applying roi")
        assert type(roi.origin[0]) is int
        assert type(roi.origin[1]) is int
        assert type(roi.size[0]) is int
        assert type(roi.size[1]) is int
        ymin, ymax = roi.origin[1], roi.origin[1] + roi.size[1]
        xmin, xmax = roi.origin[0], roi.origin[0] + roi.size[0]
        # clip roi
        ymin = max(ymin, 0)
        ymax = min(ymax, xas_obj.spectra.shape[0])
        xmin = max(xmin, 0)
        xmax = min(xmax, xas_obj.spectra.shape[1])

        assert type(ymin) is int
        assert type(ymax) is int
        assert type(xmin) is int
        assert type(xmax) is int
        # need to copy it. In orangecontrib for example for now we use the same object.
        # so if this one is modify the 'trigger / reprocessing' will be confusing to users.
        xas_obj = xas_obj.copy()
        data = xas_obj.spectra.data  # .reshape(xas_obj.spectra.shape)
        spectra = data[ymin:ymax, xmin:xmax]
        xas_obj.spectra = Spectra(
            energy=xas_obj.energy,
            spectra=spectra,
        )
        return xas_obj

    @staticmethod
    def program_name():
        return "roi"
