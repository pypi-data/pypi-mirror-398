import logging

from silx.gui import qt

from ..SpectrumPlot import SpectrumPlot
from .dialog import XASObjectDialog

_logger = logging.getLogger(__name__)


class _ToggleableSpectrumPlot(qt.QWidget):
    _BUTTON_ICON = qt.QStyle.SP_ToolBarVerticalExtensionButton

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent=parent)
        self.setLayout(qt.QGridLayout())
        self._toggleButton = qt.QPushButton(self)
        self.layout().addWidget(self._toggleButton, 0, 1, 1, 1)

        self._plot = SpectrumPlot(parent=self)
        self.layout().addWidget(self._plot, 1, 0, 1, 2)
        # set up
        self._setButtonIcon(show=True)

        # Signal / slot connection
        self._toggleButton.clicked.connect(self.toggleSpectrumPlot)

    def toggleSpectrumPlot(self):
        visible = not self._plot.isVisible()
        self._setButtonIcon(show=visible)
        self._plot.setVisible(visible)

    def _setButtonIcon(self, show):
        style = qt.QApplication.instance().style()
        # return a QIcon
        icon = style.standardIcon(self._BUTTON_ICON)
        if show is False:
            pixmap = icon.pixmap(32, 32).transformed(qt.QTransform().scale(1, -1))
            icon = qt.QIcon(pixmap)
        self._toggleButton.setIcon(icon)

    def setXasObject(self, xas_obj):
        self._plot.setXasObject(xas_obj=xas_obj)

    def clear(self):
        self._plot.clear()


class XASObjectWindow(qt.QMainWindow):
    def __init__(self, parent):
        qt.QMainWindow.__init__(self, parent)
        self.setWindowFlags(qt.Qt.Widget)
        self._mainWindow = XASObjectDialog(self)
        self.setCentralWidget(self._mainWindow)

        self._plotDW = qt.QDockWidget(self)
        self.addDockWidget(qt.Qt.BottomDockWidgetArea, self._plotDW)
        self._plotDW.setFeatures(qt.QDockWidget.DockWidgetMovable)
        self._plot = _ToggleableSpectrumPlot(self)
        self._plotDW.setWidget(self._plot)

        # connect signal / slot
        self._mainWindow.editingFinished.connect(self.loadXasObject)

    def getMainWindow(self):
        return self._mainWindow

    def setAsciiFile(self, file_path):
        self._mainWindow.setAsciiFile(file_path=file_path)

    def setEnergyColName(self, name):
        self._mainWindow.setEnergyColName(name)

    def setAbsColName(self, name):
        self._mainWindow.setAbsColName(name)

    def setMonitorColName(self, name):
        self._mainWindow.setMonitorColName(name)

    def setScanTitle(self, name):
        self._mainWindow.setScanTitle(name)

    def setCurrentType(self, input_type):
        self._mainWindow.setCurrentType(input_type=input_type)

    def setSpectraUrl(self, url):
        self._mainWindow.setSpectraUrl(url=url)

    def setEnergyUrl(self, url):
        self._mainWindow.setEnergyUrl(url=url)

    def setEnergyUnit(self, unit):
        self._mainWindow.setEnergyUnit(unit=unit)

    def setDimensions(self, dims):
        self._mainWindow.setDimensions(dims=dims)

    def setMuRefUrl(self, url):
        self._mainWindow.setMuRefUrl(url)

    def loadXasObject(self):
        """Load XasObject from information contained in the GUI
        and update plot"""
        self._plot.clear()
        try:
            xas_obj = self._mainWindow.buildXASObject()
        except Exception as e:
            _logger.error(str(e))
        else:
            if xas_obj is not None:
                self._plot.setXasObject(xas_obj=xas_obj)

    def buildXASObject(self):
        return self._mainWindow.buildXASObject()

    def getInputInformation(self):
        return self._mainWindow.getInputInformation()
