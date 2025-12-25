import logging

from ewoksorange.gui.orange_utils.orange_imports import gui
from PyMca5.PyMcaGui.physics.xas.XASNormalizationParameters import (
    XASNormalizationParameters,
)
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.pymca.normalization import PyMca_normalization
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _plot_edge
from est.gui.XasObjectViewer import _plot_norm
from est.gui.XasObjectViewer import _plot_post_edge
from est.gui.XasObjectViewer import _plot_pre_edge

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer

_logger = logging.getLogger(__file__)


class NormalizationWindow(qt.QMainWindow):
    """Widget embedding the pymca parameter window and the display of the
    data currently process"""

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # xas object viewer
        mapKeys = [
            "mu",
            "normalized_mu",
            "post_edge",
            "pre_edge",
        ]
        self.xasObjViewer = XasObjectViewer(mapKeys=mapKeys)
        self.setCentralWidget(self.xasObjViewer)
        self._pymcaWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=XASNormalizationParameters
        )
        dockWidget = qt.QDockWidget(parent=self)

        # pymca window
        dockWidget.setWidget(self._pymcaWindow)
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
        for ope in (_plot_edge, _plot_norm, _plot_post_edge, _plot_pre_edge):
            self.xasObjViewer._spectrumViews[0].addCurveOperation(ope)

        self.setWindowFlags(qt.Qt.Widget)

        # connect signal / slot
        self.xasObjViewer.viewTypeChanged.connect(self._updateLegendView)

        # set up
        self._updateLegendView()

    def getNCurves(self):
        return len(self.xasObjViewer._spectrumViews._plot.getAllCurves())

    def _updateLegendView(self):
        index, viewType = self.xasObjViewer.getViewType()
        self.legendDockWidget.setVisible(viewType is ViewType.spectrum)
        self.xasObjViewer._mapView.keySelectionDocker.setVisible(
            viewType is ViewType.map
        )


class NormalizationOW(EstProcessWidget, ewokstaskclass=PyMca_normalization):
    """
    Widget used for signal extraction
    """

    name = "normalization"
    description = "Progress spectra normalization"
    icon = "icons/normalization.png"
    priority = 1
    keywords = ["spectroscopy", "normalization"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = NormalizationWindow(parent=self)
        layout = gui.vBox(self.mainArea, "normalization").layout()
        layout.addWidget(self._window)
        self._window.xasObjViewer.setWindowTitle("spectra")

        norm_params = self.get_task_input_value("normalization", default=None)
        if norm_params is not None:
            self._window._pymcaWindow.setParameters(norm_params)

        # connect signals / slots
        pymcaWindowContainer = self._window._pymcaWindow
        pymcaWindowContainer.sigChanged.connect(self._updateProcess)

    def _updateProcess(self):
        self.update_default_inputs(
            normalization=self._window._pymcaWindow.getParameters()
        )
        self.handleNewSignals()

    def task_input_changed(self):
        xas_obj = self.get_task_input_value("xas_obj", default=None)
        if xas_obj is None:
            _logger.warning("no xas_obj. Unable to update the GUI")
            return
