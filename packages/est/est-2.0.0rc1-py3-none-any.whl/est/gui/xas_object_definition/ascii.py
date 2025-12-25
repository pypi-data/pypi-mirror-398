import logging
from typing import List

from ewoksorange.gui.qt_utils.signals import block_signals
from silx.gui import qt

from ...core.io._utils.ascii import get_all_scan_titles
from ...core.io._utils.ascii import get_scan_column_names
from ..unit.energy import EnergyUnitSelector

_logger = logging.getLogger(__name__)


class XASObjectFromAscii(qt.QWidget):
    """
    Widget used to define a XAS object from a single ASCII file.
    """

    editingFinished = qt.Signal()
    """signal emitted when edition is finished"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(qt.QGridLayout())

        # select file
        self.layout().addWidget(qt.QLabel("file", self), 0, 0, 1, 1)
        self._inputLe = _FileQLineEdit("", self)
        self.layout().addWidget(self._inputLe, 0, 1, 1, 1)
        self._selectPB = qt.QPushButton("select", self)
        self.layout().addWidget(self._selectPB, 0, 2, 1, 1)

        # select scan from multi-spectrum file
        self.layout().addWidget(qt.QLabel("scan title"), 2, 0, 1, 1)
        self._scanTitleName = _QAsciiColumnWidget(parent=self)
        self.layout().addWidget(self._scanTitleName, 2, 1, 1, 1)

        # select ASCII columns
        self._dataSelectionWidget = _QAsciiColumnsSelector(parent=self)
        self.layout().addWidget(self._dataSelectionWidget, 3, 0, 1, 2)

        # spacer
        spacer = qt.QWidget(parent=self)
        spacer.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        self.layout().addWidget(spacer, 999, 0, 1, 1)

        # signal / slot connection
        self._selectPB.pressed.connect(self._selectFile)
        self._inputLe.editingFinished.connect(self._newFileSelected)
        self._scanTitleName.currentIndexChanged.connect(self._newScanSelected)
        self._dataSelectionWidget.sigInputChanged.connect(self._editingIsFinished)

    def _editingIsFinished(self, *args, **kwargs):
        self.editingFinished.emit()

    def getFileSelected(self):
        return self._inputLe.text()

    def _getNameFilters(self):
        return [
            "Ascii (*.dat *.spec *.csv *.xmu)",
            "All Files (*)",
        ]

    def _selectFile(self, *args, **kwargs):
        dialog = qt.QFileDialog(self)
        dialog.setFileMode(qt.QFileDialog.ExistingFile)
        dialog.setNameFilters(self._getNameFilters())

        if not dialog.exec_():
            dialog.close()
            return

        fileSelected = dialog.selectedFiles()
        if len(fileSelected) == 0:
            return
        assert len(fileSelected) == 1
        self.setFileSelected(fileSelected[0])

    def setFileSelected(self, file_path):
        self._inputLe.setText(file_path)
        self._newFileSelected()

    def _newFileSelected(self):
        file_path = self.getFileSelected()
        try:
            titles = get_all_scan_titles(file_path)
        except Exception as e:
            _logger.error(
                "Retrieving scan titles from file %r failed (%s)", file_path, e
            )
            titles = []
        self._scanTitleName.setColumnNames(titles, 0)

    def _newScanSelected(self, index):
        file_path = self.getFileSelected()
        scan_title = self.getScanTitle()
        try:
            col_names = get_scan_column_names(file_path, scan_title)
        except Exception as e:
            _logger.error(
                "Retrieving column names from file %r failed (%s)", file_path, e
            )
            col_names = []
        self._dataSelectionWidget.setColumnNames(col_names)

    def getEnergyUnit(self):
        return self._dataSelectionWidget.getEnergyUnit()

    def setEnergyUnit(self, unit):
        return self._dataSelectionWidget.setEnergyUnit(unit=unit)

    def setEnergyColName(self, name):
        self._dataSelectionWidget.setEnergyColName(name)

    def getEnergyColName(self):
        return self._dataSelectionWidget.getEnergyColName()

    def setAbsColName(self, name):
        self._dataSelectionWidget.setAbsColName(name)

    def getAbsColName(self):
        return self._dataSelectionWidget.getAbsColName()

    def setMonitorColName(self, name):
        self._dataSelectionWidget.setMonitorColName(name)

    def getMonitorColName(self):
        return self._dataSelectionWidget.getMonitorColName()

    def getColumnSelected(self):
        return self._dataSelectionWidget.getColumnSelected()

    def setScanTitle(self, scan_title):
        index = self._scanTitleName.findText(scan_title)
        if index >= 0:
            self._scanTitleName.setCurrentIndex(index)

    def getScanTitle(self):
        return self._scanTitleName.currentText()

    def getMinLog(self) -> bool:
        return self._dataSelectionWidget.getMinLog()

    def setMinLog(self, value: bool) -> None:
        self._dataSelectionWidget.setMinLog(value)


class _FileQLineEdit(qt.QLineEdit):
    """QLineEdit to handle a file path"""

    def dropEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            for url in event.mimeData().urls():
                self.setText(str(url.path()))

    def supportedDropActions(self):
        """Inherited method to redefine supported drop actions."""
        return qt.Qt.CopyAction | qt.Qt.MoveAction

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            event.accept()
            event.setDropAction(qt.Qt.CopyAction)
        else:
            qt.QWidget.dragEnterEvent(self, event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            event.setDropAction(qt.Qt.CopyAction)
            event.accept()
        else:
            qt.QWidget.dragMoveEvent(self, event)


class _QAsciiColumnsSelector(qt.QWidget):
    """Select several column names from a list of ASCII column names."""

    sigInputChanged = qt.Signal()
    """Signal emitted when data selection change"""

    def __init__(self, parent):
        super().__init__(parent=parent)
        layout = qt.QGridLayout()
        self.setLayout(layout)

        self._energyColNamCB = _QAsciiColumnWidget(parent=self)
        self._energyUnitSelector = EnergyUnitSelector(parent=self)

        layout.addWidget(qt.QLabel("energy"), 0, 0)

        layout.addWidget(self._energyColNamCB, 0, 1, 1, 2)

        spacer = qt.QSpacerItem(20, 0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        layout.addItem(spacer, 0, 2)

        layout.addWidget(self._energyUnitSelector, 0, 3)

        self._absColNamCB = _QAsciiColumnWidget(parent=self)
        layout.addWidget(qt.QLabel("μ (numerator)"), 1, 0)
        layout.addWidget(self._absColNamCB, 1, 1, 1, 3)

        self._monitorColNamCB = _QAsciiColumnWidget(parent=self)
        self._monitorColNamCB.setEnabled(False)

        self._useMonitorCB = qt.QCheckBox("μ (denominator)")
        layout.addWidget(self._useMonitorCB, 2, 0)
        layout.addWidget(self._monitorColNamCB, 2, 1, 1, 3)

        self._minlogCheckbox = qt.QCheckBox("-log(numerator/denominator)", parent=self)
        self.layout().addWidget(self._minlogCheckbox, 3, 0, 1, 1)

        # connect Signal / Slot
        self._energyColNamCB.currentIndexChanged.connect(self._propagateSigChanged)
        self._absColNamCB.currentIndexChanged.connect(self._propagateSigChanged)
        self._monitorColNamCB.currentIndexChanged.connect(self._propagateSigChanged)
        self._useMonitorCB.toggled.connect(self._propagateSigChanged)
        self._useMonitorCB.toggled.connect(self._monitorColNamCB.setEnabled)
        self._energyUnitSelector.currentIndexChanged.connect(self._propagateSigChanged)
        self._minlogCheckbox.stateChanged.connect(self._propagateSigChanged)

    def _propagateSigChanged(self):
        self.sigInputChanged.emit()

    def setColumnNames(self, col_names: List[str]):
        with block_signals(self):
            self._energyColNamCB.setColumnNames(col_names, 0)
            self._absColNamCB.setColumnNames(col_names, 1)
            self._monitorColNamCB.setColumnNames(col_names, 2)
        self._propagateSigChanged()

    def getColumnSelected(self) -> dict:
        return {
            "energy": self.getEnergyColName(),
            "mu": self.getAbsColName(),
            "monitor": self.getMonitorColName(),
        }

    def getMonitorColName(self):
        if self.useMonitor():
            return self._monitorColNamCB.currentText()
        else:
            return None

    def setMonitorColName(self, name):
        with block_signals(self):
            self._monitorColNamCB.setColumnName(name)
            self._useMonitorCB.setChecked(bool(name))
        self._propagateSigChanged()

    def useMonitor(self):
        return self._useMonitorCB.isChecked()

    def setEnergyColName(self, name):
        self._energyColNamCB.setColumnName(name)

    def getEnergyColName(self):
        return self._energyColNamCB.getColumnName()

    def getEnergyUnit(self):
        return self._energyUnitSelector.getUnit()

    def setEnergyUnit(self, unit):
        return self._energyUnitSelector.setUnit(unit=unit)

    def setAbsColName(self, name):
        self._absColNamCB.setColumnName(name)

    def getAbsColName(self):
        return self._absColNamCB.getColumnName()

    def getMinLog(self) -> bool:
        return self._minlogCheckbox.isChecked()

    def setMinLog(self, value: bool) -> None:
        self._minlogCheckbox.setChecked(value)


class _QAsciiColumnWidget(qt.QComboBox):
    """Select one column names from a list of ASCII column names."""

    def __init__(self, parent):
        super().__init__(parent)

    def setColumnNames(self, columns_names: List[str], default_index: int):
        prev_name = self.getColumnName()

        self.clear()

        for column_name in columns_names:
            self.addItem(column_name)

        if len(columns_names) > default_index:
            default_name = columns_names[default_index]
        else:
            default_name = ""
        if not prev_name or self.findText(prev_name) < 0:
            prev_name = default_name

        self.setColumnName(prev_name, force_emit=True)

    def setColumnName(self, name: str, force_emit: bool = False):
        prev_index = self.currentIndex()
        index = self.findText(name)
        if name and index < 0:
            _logger.warning("ASCII column name %r not found", name)
        self.setCurrentIndex(index)
        if prev_index == index and force_emit:
            self.currentIndexChanged.emit(index)

    def getColumnName(self) -> str:
        return self.currentText()
