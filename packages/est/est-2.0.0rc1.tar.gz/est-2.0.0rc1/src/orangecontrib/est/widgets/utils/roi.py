from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt

from est.core.process.roi import ROIProcess
from est.gui.roiselector import ROISelector

from ...base import EstProcessWidget


class RoiSelectionOW(EstProcessWidget, ewokstaskclass=ROIProcess):
    """
    Widget used to make the selection of a region of Interest to treat in a
    Dataset.
    """

    name = "ROI definition"
    description = "Select data Region Of Interest"
    icon = "icons/image-select-box.svg"
    priority = 10
    keywords = ["dataset", "data", "selection", "ROI", "Region of Interest"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._widget = ROISelector(parent=self)
        layout = gui.vBox(self.mainArea, "data selection").layout()
        layout.addWidget(self._widget)

        # buttons
        types = qt.QDialogButtonBox.Ok
        self._buttons = qt.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        layout.addWidget(self._buttons)

        self._buttons.hide()

        # load settings
        self.loadSettings(
            roi_size=self.get_task_input_value("roi_size", default=None),
            roi_origin=self.get_task_input_value("roi_origin", default=None),
        )

        # connect signal / slot
        self._buttons.accepted.connect(self.validate)
        self._widget.sigRoiUpdated.connect(self._storeSettings)

    def loadSettings(self, roi_size, roi_origin):
        if roi_size is not None:
            self.setROISize(roi_size)
        if roi_origin is not None:
            self.setROIOrigin(roi_origin)

    def _storeSettings(self):
        self.update_default_inputs(
            roi_size=self.getROISize(),
            roi_origin=self.getROIOrigin(),
        )

    def task_input_changed(self, *arv, **kwargs):
        xas_obj = self.get_task_input_value("xas_obj", default=None)
        self._widget.setXasObject(xas_obj=xas_obj)
        self._buttons.show()
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

    def setROISize(self, roi_size):
        self._widget.setSize(roi_size)

    def setROIOrigin(self, roi_origin):
        self._widget.setOrigin(roi_origin)

    def handleNewSignals(self) -> None:
        """Invoked by the workflow signal propagation manager after all
        signals handlers have been called.
        """
        # for now we want to avoid propagation any processing.
        # task will be executed only when the user validates the dialog
        self.task_input_changed()
        # self.execute_ewoks_task_without_propagation()

    def getROIOrigin(self) -> tuple:
        return self._widget.getROI().getOrigin()

    def getROISize(self) -> tuple:
        return self._widget.getROI().getSize()
