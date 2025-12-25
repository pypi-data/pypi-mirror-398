from ewoksorange.gui.qt_utils.signals import block_signals
from silx.gui import qt
from silx.gui.dialog.DataFileDialog import DataFileDialog
from silx.io.url import DataUrl

from ...core.types import dimensions
from ..unit.energy import EnergyUnitSelector


class XASObjectFromH5(qt.QWidget):
    """
    Interface used to define a XAS object from h5 files and data path
    """

    editingFinished = qt.Signal()
    """signal emitted when edition is finished"""

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        layout = qt.QGridLayout()
        self.setLayout(layout)

        self._energySelector = _URLSelector(
            parent=self,
            name="energy",
            layout=layout,
            position=(0, 0),
        )

        self._energyUnit = EnergyUnitSelector(parent=self)
        layout.addWidget(self._energyUnit, 0, 3, 1, 1)

        self._spectraSelector = _URLSelector(
            parent=self, name="μ (numerator)", layout=layout, position=(1, 0)
        )

        self._muRefSelector = _URLSelector(
            parent=self, name="μ (denominator)", layout=layout, position=(2, 0)
        )

        self._minlogCheckbox = qt.QCheckBox("-log(numerator/denominator)", parent=self)
        self.layout().addWidget(self._minlogCheckbox, 3, 0, 1, 1)

        self._bufWidget = qt.QWidget(parent=self)
        self._bufWidget.setLayout(qt.QHBoxLayout())

        # Spacer to push elements
        spacer = qt.QWidget(parent=self)
        spacer.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        self._bufWidget.layout().addWidget(spacer)

        # Dimension selection widget
        self._dimensionSelection = _SpectraDimensions(parent=self._bufWidget)
        self._bufWidget.layout().addWidget(self._dimensionSelection)

        # Concatenated checkbox
        self._concatenatedCheckbox = qt.QCheckBox(
            "Concatenated spectra", parent=self._bufWidget
        )
        self._bufWidget.layout().addWidget(self._concatenatedCheckbox)

        # Labels and spin boxes
        self._concatenatedWidget = qt.QWidget(parent=self)
        self._concatenatedWidget.setLayout(qt.QVBoxLayout())

        label1 = qt.QLabel("Skip first N concatenated spectra", parent=self._bufWidget)
        self._skipConcatenatedNSpectra = qt.QSpinBox(parent=self._bufWidget)
        self._concatenatedWidget.layout().addWidget(label1)
        self._concatenatedWidget.layout().addWidget(self._skipConcatenatedNSpectra)

        label2 = qt.QLabel(
            "Trim N points of concatenated spectra",
            parent=self._bufWidget,
        )
        self._skipConcatenatedNPoints = qt.QSpinBox(parent=self._bufWidget)
        self._concatenatedWidget.layout().addWidget(label2)
        self._concatenatedWidget.layout().addWidget(self._skipConcatenatedNPoints)

        label3 = qt.QLabel(
            "Section size of concatenated spectra",
            parent=self._bufWidget,
        )
        self._concatenatedSpectraSectionSize = qt.QSpinBox(parent=self._bufWidget)
        self._concatenatedWidget.layout().addWidget(label3)
        self._concatenatedWidget.layout().addWidget(
            self._concatenatedSpectraSectionSize
        )

        self._bufWidget.layout().addWidget(self._concatenatedWidget)

        layout.addWidget(self._bufWidget, 4, 1)

        # connect signal / slot
        self._spectraSelector._qLineEdit.editingFinished.connect(
            self._editingIsFinished
        )
        self._energySelector._qLineEdit.editingFinished.connect(self._editingIsFinished)
        self._dimensionSelection.sigDimensionChanged.connect(self._editingIsFinished)
        self._energyUnit.currentIndexChanged.connect(self._editingIsFinished)
        self._concatenatedCheckbox.stateChanged.connect(
            self._onConcatenatedCheckboxChange
        )
        self._skipConcatenatedNPoints.valueChanged.connect(self._editingIsFinished)
        self._skipConcatenatedNSpectra.valueChanged.connect(self._editingIsFinished)
        self._concatenatedSpectraSectionSize.valueChanged.connect(
            self._editingIsFinished
        )
        self._muRefSelector._qLineEdit.textChanged.connect(self._editingIsFinished)
        self._minlogCheckbox.stateChanged.connect(self._editingIsFinished)

        # expose API
        self.setDimensions = self._dimensionSelection.setDimensions
        self.getDimensions = self._dimensionSelection.getDimensions

        self._syncConcatenatedCheckbox()

    def _syncConcatenatedCheckbox(self):
        concatenated = self._concatenatedCheckbox.isChecked()
        self._concatenatedWidget.setEnabled(concatenated)
        self._dimensionSelection.setDisabled(concatenated)

    def _onConcatenatedCheckboxChange(self):
        self._syncConcatenatedCheckbox()
        self._editingIsFinished()

    def getSpectraUrl(self):
        return self._spectraSelector.getUrlPath()

    def getEnergyUrl(self):
        return self._energySelector.getUrlPath()

    def setSpectraUrl(self, url):
        self._spectraSelector.setUrlPath(url)

    def setEnergyUrl(self, url):
        self._energySelector.setUrlPath(url)

    def _editingIsFinished(self, *args, **kwargs):
        self.editingFinished.emit()

    def getDimensionsInfo(self) -> dimensions.DimensionsType:
        return self._dimensionSelection.getDimensions()

    def getEnergyUnit(self):
        return self._energyUnit.getUnit()

    def setEnergyUnit(self, unit):
        self._energyUnit.setUnit(unit=unit)

    def getMuRefUrl(self):
        return self._muRefSelector.getUrlPath()

    def setMuRefUrl(self, url):
        self._muRefSelector.setUrlPath(url)

    def isSpectraConcatenated(self):
        return self._concatenatedCheckbox.isChecked()

    def setConcatenatedSpectra(self, value: bool):
        self._concatenatedCheckbox.setChecked(value)

    def getSkipConcatenatedNPoints(self):
        return self._skipConcatenatedNPoints.value()

    def setSkipConcatenatedNPoints(self, value: int):
        self._skipConcatenatedNPoints.setValue(value)

    def getSkipConcatenatedNSpectra(self):
        return self._skipConcatenatedNSpectra.value()

    def setSkipConcatenatedNSpectra(self, value: int):
        self._skipConcatenatedNSpectra.setValue(value)

    def getConcatenatedSpectraSectionSize(self):
        return self._concatenatedSpectraSectionSize.value()

    def setConcatenatedSpectraSectionSize(self, value: int):
        self._concatenatedSpectraSectionSize.setValue(value)

    def getMinLog(self) -> bool:
        return self._minlogCheckbox.isChecked()

    def setMinLog(self, value: bool) -> None:
        self._minlogCheckbox.setChecked(value)


class _QDimComboBox(qt.QComboBox):
    def __init__(self, parent):
        qt.QComboBox.__init__(self, parent)
        self.addItem("Dim 0", 0)
        self.addItem("Dim 1", 1)
        self.addItem("Dim 2", 2)
        self.setCurrentIndex(0)

    def setDim(self, dim: int):
        index = self.findData(dim)
        assert index >= 0
        self.setCurrentIndex(index)

    def getDim(self):
        return self.currentData()


class _SpectraDimensions(qt.QWidget):
    sigDimensionChanged = qt.Signal()
    """Signal emitted when dimension change"""

    def __init__(self, parent):
        qt.QWidget.__init__(self, parent=parent)
        layout = qt.QFormLayout()
        self.setLayout(layout)

        self._dim_energy = _QDimComboBox(parent=self)
        layout.addRow("Energy", self._dim_energy)
        self._dim_y = _QDimComboBox(parent=self)
        layout.addRow("Y", self._dim_y)
        self._dim_x = _QDimComboBox(parent=self)
        layout.addRow("X", self._dim_x)

        # set up
        self._dim_energy.setDim(dimensions.STANDARD_DIMENSIONS[2])
        self._dim_y.setDim(dimensions.STANDARD_DIMENSIONS[1])
        self._dim_x.setDim(dimensions.STANDARD_DIMENSIONS[0])

        # connect Signal / Slot
        self._dim_x.currentTextChanged.connect(self._ensureDimUnicity)
        self._dim_y.currentTextChanged.connect(self._ensureDimUnicity)
        self._dim_energy.currentTextChanged.connect(self._ensureDimUnicity)

    def _ensureDimUnicity(self):
        last_modified = self.sender()
        if last_modified is self._dim_x:
            get_second, get_third = self._dim_y, self._dim_energy
        elif last_modified is self._dim_y:
            get_second, get_third = self._dim_x, self._dim_energy
        elif last_modified is self._dim_energy:
            get_second, get_third = self._dim_x, self._dim_y
        else:
            raise RuntimeError("Sender should be in dim0, dim1, dim2")

        assert last_modified != get_second
        assert last_modified != get_third
        assert type(last_modified) is type(get_second) is type(get_third)
        value_set = {0, 1, 2}
        last_value_set = last_modified.getDim()
        value_set.remove(last_value_set)

        with block_signals(last_modified, get_second, get_third):
            if get_second.getDim() in value_set:
                value_set.remove(get_second.getDim())
                get_third.setDim(value_set.pop())
            elif get_third.getDim() in value_set:
                value_set.remove(get_third.getDim())
                get_second.setDim(value_set.pop())
            else:
                get_second.setDim(value_set.pop())
                get_third.setDim(value_set.pop())
        self.sigDimensionChanged.emit()

    def getDimensions(self) -> dimensions.DimensionsType:
        return (
            self._dim_x.getDim(),
            self._dim_y.getDim(),
            self._dim_energy.getDim(),
        )

    def setDimensions(self, dims: dimensions.DimensionsType) -> None:
        dims = dimensions.parse_dimensions(dims)
        self._dim_x.setDim(dims[0])
        self._dim_y.setDim(dims[1])
        self._dim_energy.setDim(dims[2])


class _URLSelector(qt.QWidget):
    def __init__(self, parent, name, layout=None, position=None):
        qt.QWidget.__init__(self, parent)
        self.name = name
        if layout is None:
            layout = self.setLayout(qt.QGridLayout())
            position = (0, 0)
        layout.addWidget(qt.QLabel(name + ":", parent=self), position[0], position[1])
        self._qLineEdit = qt.QLineEdit("", parent=self)
        layout.addWidget(self._qLineEdit, position[0], position[1] + 1)
        self._qPushButton = qt.QPushButton("select", parent=self)
        layout.addWidget(self._qPushButton, position[0], position[1] + 2)

        # connect signal / slot
        self._qPushButton.clicked.connect(self._selectFile)

    def _selectFile(self, *args, **kwargs):
        dialog = DataFileDialog(self)

        url = self._qLineEdit.text()
        if url:
            dialog.selectUrl(url)

        if not dialog.exec_():
            dialog.close()
            return None

        if dialog.selectedUrl() is not None:
            self.setUrlPath(dialog.selectedUrl())

    def getUrlPath(self):
        url = self._qLineEdit.text()
        if url == "":
            return None
        else:
            return DataUrl(path=url)

    def setUrlPath(self, url):
        if isinstance(url, DataUrl):
            url = url.path()
        self._qLineEdit.setText(url)
        self._qLineEdit.editingFinished.emit()
