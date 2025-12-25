import functools
import logging

from ewoksorange.gui.orange_utils.orange_imports import gui
from ewoksorange.gui.owwidgets.base import OWWidget
from silx.gui import qt

from est.core.process.ignoreprocess import IgnoreE0Calculation
from est.gui.e0calculator import E0Calculator
from est.gui.e0calculator import E0ComputationMethod

from ...base import EstProcessWidget

_logger = logging.getLogger(__file__)


class E0calculatorOW(EstProcessWidget, ewokstaskclass=IgnoreE0Calculation):
    """
    Widget used to make compute E0 from the dataset.
    """

    name = "e0 calculator"
    description = "Compute E0 from a region of the dataset"
    icon = "icons/e0.svg"

    priority = 25
    keywords = [
        "E0",
        "Energy",
        "dataset",
        "data",
        "selection",
        "ROI",
        "Region of Interest",
    ]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()

        self._widget = E0Calculator(parent=self)
        layout = gui.vBox(self.mainArea, "data selection").layout()
        layout.addWidget(self._widget)

        # add the buttons
        style = qt.QApplication.instance().style()
        icon = style.standardIcon(qt.QStyle.SP_DialogApplyButton)

        self._buttons = qt.QDialogButtonBox(parent=self)
        self._useMedian = qt.QPushButton(icon, "use median", self)
        self._buttons.addButton(self._useMedian, qt.QDialogButtonBox.ActionRole)
        self._useMean = qt.QPushButton(icon, "use mean", self)
        self._buttons.addButton(self._useMean, qt.QDialogButtonBox.ActionRole)
        layout.addWidget(self._buttons)

        # connect signal / slot
        self._useMean.released.connect(
            functools.partial(self.validateMethodToUse, E0ComputationMethod.MEAN)
        )
        self._useMedian.released.connect(
            functools.partial(self.validateMethodToUse, E0ComputationMethod.MEDIAN)
        )

        # set up
        self._buttons.hide()

    def validateMethodToUse(self, method):
        """Define the method to use and close the dialog"""
        method = E0ComputationMethod(method)
        assert method in (None, E0ComputationMethod.MEDIAN, E0ComputationMethod.MEAN)
        self._methodToUse = method
        self.validate()

    def getE0(self):
        if self._methodToUse is None:
            return None
        else:
            return self._widget.getE0(method=self._methodToUse)

    def task_input_changed(self):
        super().task_input_changed()
        self._buttons.show()
        self.show()

    def validate(self):
        """
        callback when the ROI has been validated
        """
        if self._widget.getXasObject() is None:
            return

        try:
            xas_obj = self._widget.getXasObject()
            prop = xas_obj.configuration
            prop["e0"] = self.getE0()
            xas_obj.configuration = prop
            _logger.info("e0 define: {}".format(str(self.getE0())))
            self.Outputs.xas_obj.send(xas_obj)
        except Exception as e:
            _logger.error(e)
        else:
            OWWidget.accept(self)
