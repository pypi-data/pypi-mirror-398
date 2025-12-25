from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt

from est.core.process.pymca.k_weight import PyMca_k_weight

from ...base import EstProcessWidget


class KWeightWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # k wright widget
        self._k_widget = qt.QWidget(parent=self)
        self._k_widget.setLayout(qt.QHBoxLayout())
        self._k_widget.layout().addWidget(qt.QLabel("k weight"))
        self._k_spin_box = qt.QSpinBox(parent=self)
        self._k_spin_box.setRange(0, 3)
        self._k_widget.layout().addWidget(self._k_spin_box)
        dockWidget = qt.QDockWidget(parent=self)
        dockWidget.setWidget(self._k_widget)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

        self.setWindowFlags(qt.Qt.Widget)


class KWeightOW(EstProcessWidget, ewokstaskclass=PyMca_k_weight):
    """
    Widget used for signal extraction
    """

    name = "k weight"
    description = "Progress k weight"
    icon = "icons/k_weight.png"
    priority = 2
    keywords = ["spectroscopy", "signal", "k", "weight"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        layout = gui.vBox(self.mainArea, "k weight").layout()
        self._window = KWeightWindow(parent=self)
        layout.addWidget(self._window)

        k_weight = self.get_task_input_value("k_weight", default=None)
        if k_weight is not None:
            self._window._k_spin_box.setValue(k_weight)

        # signal / slot connection
        self._window._k_spin_box.valueChanged.connect(self._updateProcess)

    def _updateProcess(self, *arv, **kwargs):
        self.update_default_inputs(k_weight=self._window._k_spin_box.value())
        self.handleNewSignals()
