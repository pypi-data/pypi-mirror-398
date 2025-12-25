from ewoksorange.gui.orange_utils.orange_imports import gui
from PyMca5.PyMcaGui.physics.xas.XASPostEdgeParameters import XASPostEdgeParameters
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.pymca.exafs import PyMca_exafs
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _exafs_knots_plot
from est.gui.XasObjectViewer import _exafs_postedge_plot
from est.gui.XasObjectViewer import _exafs_signal_plot

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class ExafsWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        mapKeys = [
            "mu",
            "k",
            "chi",
            ".".join(["pymca_dict", "PostEdgeB"]),
        ]
        assert isinstance("mu", str), "unexpected type"
        self.xasObjViewer = XasObjectViewer(mapKeys=mapKeys)
        self.setCentralWidget(self.xasObjViewer)

        # pymca window
        self._pymcaWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=XASPostEdgeParameters
        )
        dockWidget = qt.QDockWidget(parent=self)
        dockWidget.setWidget(self._pymcaWindow)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.setWindowFlags(qt.Qt.Widget)

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
        for ope in (_exafs_signal_plot, _exafs_postedge_plot, _exafs_knots_plot):
            self.xasObjViewer._spectrumViews[0].addCurveOperation(ope)

        self.setWindowFlags(qt.Qt.Widget)

        # connect signal / slot
        self.xasObjViewer.viewTypeChanged.connect(self._updateLegendView)

        # set up
        self._updateLegendView()

    def getNCurves(self):
        return len(self.xasObjViewer.getAllCurves())

    def _updateLegendView(self):
        index, viewType = self.xasObjViewer.getViewType()
        self.legendDockWidget.setVisible(viewType is ViewType.spectrum)
        self.xasObjViewer._mapView.keySelectionDocker.setVisible(
            viewType is ViewType.map
        )


class ExafsOW(EstProcessWidget, ewokstaskclass=PyMca_exafs):
    """
    Widget used for signal extraction
    """

    name = "exafs"
    description = "Progress signal extraction"
    icon = "icons/exafs.png"
    priority = 3
    keywords = ["spectroscopy", "signal"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = ExafsWindow()
        layout = gui.vBox(self.mainArea, "exafs").layout()
        layout.addWidget(self._window)
        exafs_params = self.get_task_input_value("exafs", default=None)
        if exafs_params is not None:
            self._window._pymcaWindow.setParameters(exafs_params)

        # signal / slot connection
        self._window._pymcaWindow.sigChanged.connect(self._updateProcess)

    def _updateProcess(self):
        self.update_default_inputs(exafs=self._window._pymcaWindow.getParameters())
        self.handleNewSignals()
