from silx.gui import qt

from .XasObjectViewer import SpectrumViewer
from .XasObjectViewer import plot_spectrum


class SpectrumPlot(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QHBoxLayout())

        self._plot = SpectrumViewer(self)

        self._plot.addCurveOperation(plot_spectrum)
        self._plot.setWindowFlags(qt.Qt.Widget)
        # self._plot.setVisible(True)
        self.layout().addWidget(self._plot)

        # expose API
        self.addXMarker = self._plot._plotWidget.addXMarker

    def setXasObject(self, xas_obj):
        self._plot.setXasObject(xas_obj=xas_obj)

    def clear(self):
        self._plot.setXasObject(None)
