from silx.gui import qt


class _OptionalQDoubleSpinBox(qt.QWidget):
    """
    Simple widget allowing to activate or tnoe the spin box
    """

    sigChanged = qt.Signal()
    """Signal emitted when parameters changed"""

    def __init__(self, parent):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QHBoxLayout())
        self._checkbox = qt.QCheckBox(parent=self)
        self.layout().addWidget(self._checkbox)
        self._spinBox = qt.QDoubleSpinBox(parent=self)
        self.layout().addWidget(self._spinBox)

        # default set up
        self._checkbox.setChecked(True)
        self._spinBox.setMinimum(-999999)
        self._spinBox.setMaximum(999999)
        self._lastValue = None

        # connect signal / slot
        self._checkbox.toggled.connect(self._updateSpinBoxStatus)
        self._spinBox.editingFinished.connect(self._valueChanged)

    def getValue(self):
        if self._checkbox.isChecked():
            return self._spinBox.value()
        else:
            return None

    def setValue(self, value):
        self._checkbox.setChecked(value is not None)
        if value is not None:
            self._spinBox.setValue(value)

    def _updateSpinBoxStatus(self, *arg, **kwargs):
        self._spinBox.setEnabled(self._checkbox.isChecked())
        self._valueChanged()

    def _valueChanged(self, *arg, **kwargs):
        if self._lastValue != self.getValue():
            self._lastValue = self.getValue()
            self.sigChanged.emit()

    # expose API

    def setMinimum(self, value):
        self._spinBox.setMinimum(value)

    def setMaximun(self, value):
        self._spinBox.setMaximun(value)

    def setSingleStep(self, value):
        self._spinBox.setSingleStep(value)

    def setRange(self, v1, v2):
        self._spinBox.setRange(v1, v2)

    def setSuffix(self, suffix):
        self._spinBox.setSuffix(suffix)


class _OptionalQIntSpinBox(qt.QWidget):
    """
    Simple widget allowing to activate or tnoe the spin box
    """

    sigChanged = qt.Signal()
    """Signal emitted when parameters changed"""

    def __init__(self, parent):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QHBoxLayout())
        self._checkbox = qt.QCheckBox(parent=self)
        self.layout().addWidget(self._checkbox)
        self._spinBox = qt.QSpinBox(parent=self)
        self.layout().addWidget(self._spinBox)

        # default set up
        self._checkbox.setChecked(True)
        self._lastValue = None

        # expose API
        self.setMinimum = self._spinBox.setMinimum
        self.setMaximum = self._spinBox.setMaximum
        self.setRange = self._spinBox.setRange

        # connect signal / slot
        self._checkbox.toggled.connect(self._updateSpinBoxStatus)
        self._spinBox.valueChanged.connect(self._valueChanged)

    def getValue(self):
        if self._checkbox.isChecked():
            return self._spinBox.value()
        else:
            return None

    def setValue(self, value):
        self._checkbox.setChecked(value is not None)
        if value is not None:
            self._spinBox.setValue(value)

    def _updateSpinBoxStatus(self, *arg, **kwargs):
        self._spinBox.setEnabled(self._checkbox.isChecked())
        self._valueChanged()

    def _valueChanged(self, *arg, **kwargs):
        if self._lastValue != self.getValue():
            self._lastValue = self.getValue()
            self.sigChanged.emit()
