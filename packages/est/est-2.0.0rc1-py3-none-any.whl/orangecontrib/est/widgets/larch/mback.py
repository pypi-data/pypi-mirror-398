from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.larch.mback import Larch_mback
from est.gui.larch.mback import _MBackParameters
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _plot_f2
from est.gui.XasObjectViewer import _plot_fpp
from est.gui.XasObjectViewer import _plot_norm
from est.gui.XasObjectViewer import _plot_raw

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class MbackWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # xas object viewer
        mapKeys = ["mu", "fpp", "f2"]
        self.xasObjViewer = XasObjectViewer(mapKeys=mapKeys)
        self.setCentralWidget(self.xasObjViewer)
        self._parametersWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=_MBackParameters
        )
        dockWidget = qt.QDockWidget(parent=self)

        # parameters window
        dockWidget.setWidget(self._parametersWindow)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

        # legend selector
        self.legendDockWidget = LegendSelector.LegendsDockWidget(
            parent=self, plot=self.xasObjViewer._spectrumViews[0]._plotWidget
        )
        self.legendDockWidget.setAllowedAreas(
            qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea
        )
        self.legendDockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self.legendDockWidget)

        # volume key selection
        self.addDockWidget(
            qt.Qt.RightDockWidgetArea, self.xasObjViewer._mapView.keySelectionDocker
        )

        # plot settings
        for ope in (_plot_fpp, _plot_f2, _plot_raw, _plot_norm):
            self.xasObjViewer._spectrumViews[0].addCurveOperation(ope)

        self.setWindowFlags(qt.Qt.Widget)

        # connect signal / slot
        self.xasObjViewer.viewTypeChanged.connect(self._updateLegendView)

        # set up
        self._updateLegendView()

    def _updateLegendView(self):
        index, viewType = self.xasObjViewer.getViewType()
        self.legendDockWidget.setVisible(viewType is ViewType.spectrum)
        self.xasObjViewer._mapView.keySelectionDocker.setVisible(
            viewType is ViewType.map
        )

    def getNCurves(self):
        return len(self.xasObjViewer._spectrumViews[0]._plotWidget.getAllCurves())


class MbackOW(EstProcessWidget, ewokstaskclass=Larch_mback):
    """
    Widget used for signal extraction
    """

    name = "mback"
    description = (
        "Match mu(E) data for tabulated f''(E) using the MBACK "
        "algorithm and, optionally, the Lee & Xiang extension"
    )
    icon = "icons/mback.svg"
    priority = 5
    keywords = ["spectroscopy", "mback"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = MbackWindow(parent=self)
        layout = gui.vBox(self.mainArea, "mback").layout()
        layout.addWidget(self._window)
        self._window.xasObjViewer.setWindowTitle("spectra")

        # manage settings
        larch_settings = self.get_task_input_value("mback_config", default=None)
        if larch_settings is None:
            larch_settings = self.getParameters()
        self.loadSettings(larch_settings)

        # connect signals / slots
        self._window._parametersWindow.sigChanged.connect(self._updateProcess)

    def _updateProcess(self):
        self.update_default_inputs(mback=self._window._parametersWindow.getParameters())
        self.handleNewSignals()

    def loadSettings(self, settings):
        self._window._parametersWindow.setParameters(settings)
        self.update_default_inputs(mback_config=self.getParameters())

    def getParameters(self):
        return self._window._parametersWindow.getParameters()
