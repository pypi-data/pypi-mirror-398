from ewoksorange.gui.orange_utils.orange_imports import gui
from PyMca5.PyMcaGui.physics.xas.XASFourierTransformParameters import (
    XASFourierTransformParameters,
)
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.pymca.ft import PyMca_ft
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _ft_imaginary_plot
from est.gui.XasObjectViewer import _ft_intensity_plot
from est.gui.XasObjectViewer import _ft_window_plot
from est.gui.XasObjectViewer import _normalized_exafs

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class FTWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        assert isinstance("mu", str)

        # xas object viewer
        self.xasObjViewer = XasObjectViewer(
            mapKeys=[
                "mu",
            ],
            spectrumPlots=("FTWindow", "FTIntensity"),
        )
        self.setCentralWidget(self.xasObjViewer)
        self._pymcaWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=XASFourierTransformParameters
        )
        dockWidget = qt.QDockWidget(parent=self)

        # pymca window
        dockWidget.setWidget(self._pymcaWindow)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

        # legend selectors
        self.legendDockWidget1 = LegendSelector.LegendsDockWidget(
            parent=self, plot=self.xasObjViewer._spectrumViews[0]._plotWidget
        )
        self.legendDockWidget1.setAllowedAreas(
            qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea
        )
        self.legendDockWidget1.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self.legendDockWidget1)

        self.legendDockWidget2 = LegendSelector.LegendsDockWidget(
            parent=self, plot=self.xasObjViewer._spectrumViews[1]._plotWidget
        )
        self.legendDockWidget2.setAllowedAreas(
            qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea
        )
        self.legendDockWidget2.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self.legendDockWidget2)

        # volume key selection
        self.addDockWidget(
            qt.Qt.RightDockWidgetArea, self.xasObjViewer._mapView.keySelectionDocker
        )

        # plot settings
        for ope in (_normalized_exafs, _ft_window_plot):
            self.xasObjViewer._spectrumViews[0].addCurveOperation(ope)

        for ope in (_ft_intensity_plot, _ft_imaginary_plot):
            self.xasObjViewer._spectrumViews[1].addCurveOperation(ope)

        self.setWindowFlags(qt.Qt.Widget)

        # connect signal / slot
        self.xasObjViewer.viewTypeChanged.connect(self._updateLegendView)

        # set up
        self._updateLegendView()

    def getNCurves(self):
        return len(self.plot.getAllCurves())

    def _updateLegendView(self):
        index, viewType = self.xasObjViewer.getViewType()
        self.legendDockWidget1.setVisible(viewType is ViewType.spectrum and index == 0)
        self.legendDockWidget2.setVisible(viewType is ViewType.spectrum and index == 1)
        self.xasObjViewer._mapView.keySelectionDocker.setVisible(
            viewType is ViewType.map
        )


class FTOW(EstProcessWidget, ewokstaskclass=PyMca_ft):
    """
    Widget used for signal extraction
    """

    name = "fourier transform"
    description = "Progress fourier transform"
    icon = "icons/ft.png"
    priority = 4
    keywords = ["spectroscopy", "signal", "fourier", "transform", "fourier transform"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = FTWindow(parent=self)
        layout = gui.vBox(self.mainArea, "fourier transform").layout()
        layout.addWidget(self._window)

        ft_params = self.get_task_input_value("ft", default=None)
        if ft_params is not None:
            self._window._pymcaWindow.setParameters(ft_params)

        # signal / slot connection
        self._window._pymcaWindow.sigChanged.connect(self._updateProcess)

    def _updateProcess(self, *arv, **kwargs):
        self.update_default_inputs(ft=self._window._pymcaWindow.getParameters())
        self.handleNewSignals()
