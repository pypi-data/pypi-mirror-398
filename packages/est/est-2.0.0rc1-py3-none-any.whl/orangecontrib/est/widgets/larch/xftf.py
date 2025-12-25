from ewoksorange.gui.orange_utils.orange_imports import gui
from silx.gui import qt
from silx.gui.plot import LegendSelector

from est.core.process.larch.xftf import Larch_xftf
from est.gui.larch.xftf import _MXFTFParameters
from est.gui.XasObjectViewer import ViewType
from est.gui.XasObjectViewer import XasObjectViewer
from est.gui.XasObjectViewer import _plot_chi_weighted_k
from est.gui.XasObjectViewer import _plot_chir_imag
from est.gui.XasObjectViewer import _plot_chir_mag
from est.gui.XasObjectViewer import _plot_chir_re

from ...base import EstProcessWidget
from ..container import _ParameterWindowContainer


class XFTFWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # xas object viewer
        mapKeys = [
            "mu",
            "chir",
            "chir_mag",
            "chir_re",
            "chir_im",
            "chir_pha",
        ]
        self.xasObjViewer = XasObjectViewer(
            mapKeys=mapKeys, spectrumPlots=("FT(R)", "k^n chi(k)")
        )
        self.setCentralWidget(self.xasObjViewer)
        self._parametersWindow = _ParameterWindowContainer(
            parent=self, parametersWindow=_MXFTFParameters
        )
        dockWidget = qt.QDockWidget(parent=self)

        # parameters window
        dockWidget.setWidget(self._parametersWindow)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

        # FT legend selector
        self._ftLegendDockWidget = LegendSelector.LegendsDockWidget(
            parent=self, plot=self.xasObjViewer._spectrumViews[0]._plotWidget
        )
        self._ftLegendDockWidget.setAllowedAreas(
            qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea
        )
        self._ftLegendDockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self._ftLegendDockWidget)

        # volume key selection
        self.addDockWidget(
            qt.Qt.RightDockWidgetArea, self.xasObjViewer._mapView.keySelectionDocker
        )

        # plot settings
        for ope in (_plot_chir_mag, _plot_chir_re, _plot_chir_imag):
            self.xasObjViewer._spectrumViews[0].addCurveOperation(ope)
        self.xasObjViewer._spectrumViews[1].addCurveOperation(_plot_chi_weighted_k)
        self.setWindowFlags(qt.Qt.Widget)

        # connect signal / slot
        self.xasObjViewer.viewTypeChanged.connect(self._updateLegendView)

        # set up
        self._updateLegendView()

    def _updateLegendView(self):
        index, viewType = self.xasObjViewer.getViewType()
        self._ftLegendDockWidget.setVisible(
            viewType is ViewType.spectrum and index == 0
        )
        self.xasObjViewer._mapView.keySelectionDocker.setVisible(
            viewType is ViewType.map
        )

    def getNCurves(self):
        return len(self.xasObjViewer._spectrumViews[0]._plotWidget.getAllCurves())

    def setKWeight(self, kweight):
        self._parametersWindow._mainwidget.setRWeight(kweight)


class XFTFOW(EstProcessWidget, ewokstaskclass=Larch_xftf):
    """
    Widget used for signal extraction
    """

    name = "xftf"
    description = (
        "forward XAFS Fourier transform, from chi(k) to chi(R), "
        "using common XAFS conventions."
    )
    icon = "icons/xftf.png"
    priority = 2
    keywords = ["spectroscopy", "xftf", "fourier transform"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = XFTFWindow(parent=self)
        layout = gui.vBox(self.mainArea, "xftf").layout()
        layout.addWidget(self._window)
        self._window.xasObjViewer.setWindowTitle("spectra")

        # manage settings
        xftf_settings = self.get_task_input_value("xftf_config", default=None)
        if xftf_settings is None:
            xftf_settings = self.getParameters()
        self.loadSettings(xftf_settings)

        # connect signals / slots
        self._window._parametersWindow.sigChanged.connect(self._updateProcess)

    def loadSettings(self, settings):
        self._window._parametersWindow.setParameters(settings)
        self.update_default_inputs(xftf_config=self.getParameters())

    def _updateProcess(self):
        self.update_default_inputs(xftf_config=self.getParameters())
        self.handleNewSignals()

    def getParameters(self):
        return self._window._parametersWindow.getParameters()
