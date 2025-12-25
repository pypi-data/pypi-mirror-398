from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt
from silx.gui.plot import LegendSelector

import est.core.process.larch.mback_norm
from est.gui.larch.mback import _MBackParameters
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _plot_mback_mu
from est.gui.XasObjectViewer import _plot_norm

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class Mback_normWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # xas object viewer
        mapKeys = [
            "mu",
            "pre_edge",
            "normalized_mu",
        ]
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
        for ope in (_plot_mback_mu, _plot_norm):
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


class Mback_normOW(
    EstProcessWidget, ewokstaskclass=est.core.process.larch.mback_norm.Larch_mback_norm
):
    """
    Widget used for signal extraction
    """

    name = "mback norm"
    description = (
        "simplified version of MBACK to Match mu(E) data for "
        "tabulated f''(E) for normalization"
    )
    icon = "icons/mbacknorm.svg"
    priority = 6
    keywords = ["spectroscopy", "mback_norm"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = Mback_normWindow(parent=self)
        layout = gui.vBox(self.mainArea, "mback_norm").layout()
        layout.addWidget(self._window)
        self._window.xasObjViewer.setWindowTitle("spectra")

        # manage settings
        larch_settings = self.get_task_input_value("mback_norm_config", default=None)
        if larch_settings is None:
            larch_settings = self.getParameters()

        self.loadSettings(larch_settings)

        # connect signals / slots
        self._window._parametersWindow.sigChanged.connect(self._updateProcess)

    def _updateProcess(self):
        self.update_default_inputs(mback_norm_config=self.getParameters())
        self.handleNewSignals()

    def loadSettings(self, settings):
        self._window._parametersWindow.setParameters(settings)
        self.update_default_inputs(mback_norm_config=self.getParameters())

    def getParameters(self):
        return self._window._parametersWindow.getParameters()
