from typing import Optional
from typing import Tuple

from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt

from est.core.process.energyroi import EnergyROIProcess
from est.gui.energyroi import EnergyRoiWidget

from ...base import EstProcessWidget


class EnergyRoiOW(EstProcessWidget, ewokstaskclass=EnergyROIProcess):
    """
    Widget used to make the selection of a region of Interest to treat in a
    Dataset.
    """

    name = "energy ROI"
    description = "Select the energy ROI to analyse"
    icon = "icons/curveroi.svg"

    priority = 8
    keywords = [
        "dataset",
        "data",
        "selection",
        "ROI",
        "Region of Interest",
        "energy ROI",
        "energy",
    ]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()

        self._widget = EnergyRoiWidget(parent=self)
        layout = gui.vBox(self.mainArea, "energy roi").layout()
        layout.addWidget(self._widget)

        # buttons
        types = qt.QDialogButtonBox.Ok
        self._buttons = qt.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        layout.addWidget(self._buttons)

        energy_roi = self.get_task_input_value(
            "energy_roi", default={"minE": None, "maxE": None}
        )
        if energy_roi is None:
            # Deprecated
            energy_roi = {"minE": None, "maxE": None}

        self.loadSettings(energy_roi=energy_roi)

        # connect signal / slot
        self._buttons.accepted.connect(self.validate)
        self._widget.sigROIChanged.connect(self._storeSettings)

    def _storeSettings(self):
        minE, maxE = self.getROI()
        self.update_default_inputs(energy_roi={"minE": minE, "maxE": maxE})

    def loadSettings(self, energy_roi: dict):
        minE = energy_roi["minE"]
        maxE = energy_roi["maxE"]
        self.setROI((minE, maxE))
        self._widget._updateROIAnchors()

    def getROI(self) -> Tuple[Optional[float], Optional[float]]:
        return self._widget.getROI()

    def setROI(self, roi: Tuple[Optional[float], Optional[float]]):
        self._widget.setROI(roi=roi)

    def task_input_changed(self, *arv, **kwargs):
        xas_obj = self.get_task_input_value("xas_obj", default=None)
        self._widget.setXasObject(xas_obj=xas_obj)
        self.show()
        super().task_input_changed(*arv, **kwargs)

    def validate(self):
        """
        callback when the ROI has been validated
        """
        xas_obj = self._widget.getXasObject()
        if xas_obj is not None:
            self.execute_ewoks_task()
            super().accept()

    def handleNewSignals(self) -> None:
        """Invoked by the workflow signal propagation manager after all
        signals handlers have been called.
        """
        # for now we want to avoid propagation any processing.
        # task will be executed only when the user validates the dialog
        self.task_input_changed()
        # self.execute_ewoks_task_without_propagation()
