"""Tools to select energy roi"""

from typing import Optional
from typing import Tuple
from typing import Union

from ewoksorange.gui.qt_utils.signals import block_signals
from silx.gui import qt

from ..core.types.xasobject import XASObject
from .SpectrumPlot import SpectrumPlot


class _RoiSettings(qt.QWidget):
    sigValueChanged = qt.Signal()
    """signal emitted when roi value is changed"""

    MAX_VALUE = 999999999

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        layout = qt.QFormLayout()
        self.setLayout(layout)

        # Min E
        self._minE = qt.QDoubleSpinBox(self)
        self._minE.setRange(0, _RoiSettings.MAX_VALUE)
        self._minE.setValue(0)
        self._minEEnable = qt.QCheckBox("Bounded", self)
        self._minEEnable.setChecked(True)
        minLayout = qt.QHBoxLayout()
        minLayout.addWidget(self._minE)
        minLayout.addWidget(self._minEEnable)
        layout.addRow("min E", minLayout)

        # Max E
        self._maxE = qt.QDoubleSpinBox(self)
        self._maxE.setRange(0, _RoiSettings.MAX_VALUE)
        self._maxE.setValue(_RoiSettings.MAX_VALUE)
        self._maxEEnable = qt.QCheckBox("Bounded", self)
        self._maxEEnable.setChecked(True)
        maxLayout = qt.QHBoxLayout()
        maxLayout.addWidget(self._maxE)
        maxLayout.addWidget(self._maxEEnable)
        layout.addRow("max E", maxLayout)

        # connect signal / slot
        self._minE.editingFinished.connect(self._changed)
        self._maxE.editingFinished.connect(self._changed)
        self._minEEnable.stateChanged.connect(self._onMinEnableChanged)
        self._maxEEnable.stateChanged.connect(self._onMaxEnableChanged)

    def _changed(self) -> None:
        self.sigValueChanged.emit()

    def _onMinEnableChanged(self, state) -> None:
        self._minE.setEnabled(state == qt.Qt.Checked)
        self._changed()

    def _onMaxEnableChanged(self, state) -> None:
        self._maxE.setEnabled(state == qt.Qt.Checked)
        self._changed()

    def setRangeE(self, min_E: Optional[float], max_E: Optional[float]) -> None:
        with block_signals(self):
            self.setMinE(min_E)
            self.setMaxE(max_E)
        self.sigValueChanged.emit()

    def _setRangeE(self, min_E: float, max_E: float) -> None:
        with block_signals(self):
            self._minE.setValue(min_E)
            self._maxE.setValue(max_E)
        self.sigValueChanged.emit()

    def getMinE(self) -> Optional[float]:
        return self._minE.value() if self._minEEnable.isChecked() else None

    def setMinE(self, value: Optional[float]) -> None:
        if value is None:
            self._minEEnable.setChecked(False)
        else:
            self._minEEnable.setChecked(True)
            self._minE.setValue(value)

    def getMaxE(self) -> Optional[float]:
        return self._maxE.value() if self._maxEEnable.isChecked() else None

    def setMaxE(self, value: Optional[float]) -> None:
        if value is None:
            self._maxEEnable.setChecked(False)
        else:
            self._maxEEnable.setChecked(True)
            self._maxE.setValue(value)

    def getROI(self) -> Tuple[Optional[float], Optional[float]]:
        return self.getMinE(), self.getMaxE()

    def setROI(self, roi: Tuple[Optional[float], Optional[float]]) -> None:
        min, max = roi
        self.setMinE(min)
        self.setMaxE(max)

    def trimROI(self, min_E: float, max_E: float) -> None:
        current_minE = self._minE.value()
        reset_minE = current_minE == 0 or current_minE < min_E
        current_maxE = self._maxE.value()
        reset_maxE = current_maxE == self.MAX_VALUE or current_maxE > max_E
        if reset_minE or reset_maxE:
            self._setRangeE(min_E, max_E)


class EnergyRoiWidget(qt.QMainWindow):
    sigROIChanged = qt.Signal()
    """signal emit when the ROI is updated"""

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        self.setWindowFlags(qt.Qt.Widget)

        # plot
        self._plot = SpectrumPlot(self)
        self.setCentralWidget(self._plot)

        # roi settings
        self._widget = _RoiSettings(self)
        dockWidget = qt.QDockWidget(parent=self)
        dockWidget.setWidget(self._widget)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setAllowedAreas(qt.Qt.RightDockWidgetArea | qt.Qt.LeftDockWidgetArea)
        dockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

        # add Markers
        self._minEMarker = self._plot.addXMarker(
            self._widget.getMinE(),
            legend="from",
            color="red",
            draggable=True,
            text="min E",
        )

        self._maxEMarker = self._plot.addXMarker(
            self._widget.getMaxE(),
            legend="to",
            color="red",
            draggable=True,
            text="max E",
        )

        # expose API
        self.setROI = self._widget.setROI
        self.getROI = self._widget.getROI

        # connect signal / slot
        self._widget.sigValueChanged.connect(self._updateROIAnchors)
        self._getMinMarker().sigDragFinished.connect(self._updateMinValuefromMarker)
        self._getMaxMarker().sigDragFinished.connect(self._updateMaxValuefromMarker)

    def setXasObject(self, xas_obj: Union[XASObject, dict, None]):
        if xas_obj is None:
            self._plot.clear()
        else:
            if isinstance(xas_obj, dict):
                xas_obj = XASObject.from_dict(xas_obj)
            if not isinstance(xas_obj, XASObject):
                raise TypeError(str(type(xas_obj)))
            self._plot.setXasObject(xas_obj)
            if xas_obj.energy is not None and xas_obj.energy.size:
                self._widget.trimROI(xas_obj.energy.min(), xas_obj.energy.max())

    def getXasObject(self) -> Optional[XASObject]:
        return self._plot._plot.xas_obj

    def _getMinMarker(self):
        return self._plot._plot._plotWidget._getMarker(self._minEMarker)

    def _getMaxMarker(self):
        return self._plot._plot._plotWidget._getMarker(self._maxEMarker)

    def _updateROIAnchors(self):
        min_marker = self._getMinMarker()
        max_marker = self._getMaxMarker()

        with block_signals(min_marker, max_marker):
            value = self._widget.getMinE()
            if value is None:
                min_marker.setVisible(False)
            else:
                min_marker.setVisible(True)
                min_marker.setPosition(value, 0)

            value = self._widget.getMaxE()
            if value is None:
                max_marker.setVisible(False)
            else:
                max_marker.setVisible(True)
                max_marker.setPosition(value, 0)

        self.sigROIChanged.emit()

    def _updateMinValuefromMarker(self):
        with block_signals(self._widget):
            self._widget.setMinE(self._getMinMarker().getPosition()[0])
        self.sigROIChanged.emit()

    def _updateMaxValuefromMarker(self):
        with block_signals(self._widget):
            self._widget.setMaxE(self._getMaxMarker().getPosition()[0])
        self.sigROIChanged.emit()
