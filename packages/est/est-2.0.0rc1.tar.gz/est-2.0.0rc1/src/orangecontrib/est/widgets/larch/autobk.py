from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.larch.autobk import Larch_autobk
from est.gui.larch.autobk import _AutobkParameters
from est.gui.XasObjectViewer import (
    ViewType,  # _plot_knots,  # some parameters required for it does not exists anymore
)
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _plot_bkg
from est.gui.XasObjectViewer import _plot_chi
from est.gui.XasObjectViewer import plot_spectrum

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class AutobkWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # xas object viewer
        mapKeys = [
            "mu",
            "bkg",
            "chie",
            "k",
            "chi",
            "e0",
        ]
        self.xasObjViewer = XasObjectViewer(
            mapKeys=mapKeys, spectrumPlots=("background", "chi(k)")
        )
        self.setCentralWidget(self.xasObjViewer)
        self._parametersWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=_AutobkParameters
        )
        dockWidget = qt.QDockWidget(parent=self)

        # parameters window
        dockWidget.setWidget(self._parametersWindow)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

        # bkg legend selector
        self.bkgLegendDockWidget = LegendSelector.LegendsDockWidget(
            parent=self, plot=self.xasObjViewer._spectrumViews[0]._plotWidget
        )
        self.bkgLegendDockWidget.setAllowedAreas(
            qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea
        )
        self.bkgLegendDockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self.bkgLegendDockWidget)

        # chi legend selector
        self._chiLegendDockWidget = LegendSelector.LegendsDockWidget(
            parent=self, plot=self.xasObjViewer._spectrumViews[1]._plotWidget
        )
        self._chiLegendDockWidget.setAllowedAreas(
            qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea
        )
        self._chiLegendDockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self._chiLegendDockWidget)

        # volume key selection
        self.addDockWidget(
            qt.Qt.RightDockWidgetArea, self.xasObjViewer._mapView.keySelectionDocker
        )

        # plot settings
        # for ope in (_plot_bkg, plot_spectrum, _plot_knots):  # plot_knots does not exists anymore. Missing parameter from larch
        for ope in (_plot_bkg, plot_spectrum):
            self.xasObjViewer._spectrumViews[0].addCurveOperation(ope)

        self.xasObjViewer._spectrumViews[1].addCurveOperation(_plot_chi)

        self.setWindowFlags(qt.Qt.Widget)

        # connect signal / slot
        self.xasObjViewer.viewTypeChanged.connect(self._updateLegendView)

        # set up
        self._updateLegendView()

    def getNCurves(self):
        return len(self.xasObjViewer._spectrumViews[0]._plotWidget.getAllCurves())

    def _updateLegendView(self):
        index, viewType = self.xasObjViewer.getViewType()
        self.bkgLegendDockWidget.setVisible(
            viewType is ViewType.spectrum and index == 0
        )
        self._chiLegendDockWidget.setVisible(
            viewType is ViewType.spectrum and index == 1
        )
        self.xasObjViewer._mapView.keySelectionDocker.setVisible(
            viewType is ViewType.map
        )


class AutobkOW(EstProcessWidget, ewokstaskclass=Larch_autobk):
    """
    Widget used for signal extraction
    """

    name = "autobk"
    description = "background removal"
    icon = "icons/autobk.png"
    priority = 1
    keywords = ["spectroscopy", "autobk", "background"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = AutobkWindow(parent=self)
        layout = gui.vBox(self.mainArea, "autobk").layout()
        layout.addWidget(self._window)
        self._window.xasObjViewer.setWindowTitle("spectra")

        # manage settings
        larch_settings = self.get_task_input_value("autobk_config", default=None)
        if larch_settings is None:
            # ensure task with have some default input if not interaction with the window
            larch_settings = self.getParameters()
        self.loadSettings(larch_settings)

        # connect signals / slots
        self._window._parametersWindow.sigChanged.connect(self._updateProcess)

    def loadSettings(self, settings):
        self._window._parametersWindow.setParameters(settings)
        self.update_default_inputs(autobk_config=self.getParameters())

    def _updateProcess(self):
        """Update settings keeping current xas obj"""
        self.update_default_inputs(autobk_config=self.getParameters())
        self.handleNewSignals()

    def getParameters(self):
        return self._window._parametersWindow.getParameters()
