from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.larch.pre_edge import Larch_pre_edge
from est.gui.larch.pre_edge import _MPreEdgeParameters
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _plot_edge
from est.gui.XasObjectViewer import _plot_flatten_mu
from est.gui.XasObjectViewer import _plot_norm
from est.gui.XasObjectViewer import _plot_post_edge
from est.gui.XasObjectViewer import _plot_pre_edge
from est.gui.XasObjectViewer import _plot_raw

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class _PreEdgeWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # xas object viewer
        mapKeys = ["mu", "normalized_energy"]
        self.xasObjViewer = XasObjectViewer(mapKeys=mapKeys)
        self.setCentralWidget(self.xasObjViewer)
        self._parametersWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=_MPreEdgeParameters
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
        for ope in (
            _plot_raw,
            _plot_norm,
            _plot_flatten_mu,
            _plot_pre_edge,
            _plot_post_edge,
            _plot_edge,
        ):
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


class PreEdgeOW(EstProcessWidget, ewokstaskclass=Larch_pre_edge):
    """
    Widget used for signal extraction
    """

    name = "pre edge"
    description = """
    pre edge subtraction, normalization for XAFS
    This performs a number of steps:
       1. determine E0 (if not supplied) from max of deriv(mu)
       2. fit a line of polynomial to the region below the edge
       3. fit a polynomial to the region above the edge
       4. extrapolate the two curves to E0 to determine the edge jump
       5. estimate area from emin_area to norm2, to get norm_area
    """
    icon = "icons/pre_edge.png"
    priority = 2
    keywords = ["spectroscopy", "preedge", "pre", "edge", "normalization"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = _PreEdgeWindow(parent=self)
        layout = gui.vBox(self.mainArea, "pre edge").layout()
        layout.addWidget(self._window)
        self._window.xasObjViewer.setWindowTitle("spectra")

        # manage settings
        larch_settings = self.get_task_input_value("pre_edge_config", default=None)
        if larch_settings is None:
            larch_settings = self.getParameters()
        self.loadSettings(larch_settings)

        # connect signals / slots
        self._window._parametersWindow.sigChanged.connect(self._updateProcess)

    def _updateProcess(self):
        self.update_default_inputs(pre_edge_config=self.getParameters())
        self.handleNewSignals()

    def loadSettings(self, settings):
        self._window._parametersWindow.setParameters(settings)
        self.update_default_inputs(pre_edge_config=self.getParameters())

    def getParameters(self):
        return self._window._parametersWindow.getParameters()
