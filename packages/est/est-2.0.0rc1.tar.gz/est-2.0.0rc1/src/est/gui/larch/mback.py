from silx.gui import qt

from .utils import _OptionalQDoubleSpinBox


class _MBackParameters(qt.QWidget):
    """
    Widget for setting the configuration of the larch 'mback' process
    """

    sigChanged = qt.Signal()
    """Signal emitted when parameters changed"""

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QFormLayout())

        # z
        self._atomicNumberSB = qt.QSpinBox(parent=self)
        self._atomicNumberSB.setToolTip("atomic number of the absorber")
        self._atomicNumberSB.setMinimum(1)
        self._atomicNumberSB.setValue(13)
        self._atomicNumberSB.setMaximum(118)
        self.layout().addRow(qt.QLabel("z", parent=self), self._atomicNumberSB)
        # edge
        self._edgeCB = qt.QComboBox(parent=self)
        for val in ("K", "L1", "L2", "L3", "M1", "M2", "M3", "M4", "M5"):
            self._edgeCB.addItem(val)
        index = self._edgeCB.findText("K")
        assert index >= 0
        self._edgeCB.setCurrentIndex(index)
        self._edgeCB.setToolTip("x-ray absorption edge")
        self.layout().addRow(qt.QLabel("edge", parent=self), self._edgeCB)
        # e0
        self._e0SB = _OptionalQDoubleSpinBox(parent=self)
        self._e0SB.setToolTip(
            "edge energy, in eV.  If None, it will be " "determined here."
        )
        self._e0SB.setMinimum(0.0)
        self._e0SB.setValue(2000.0)
        self._e0SB.setValue(None)
        self.layout().addRow(qt.QLabel("e0", parent=self), self._e0SB)
        # pre1
        self._pre1SB = _OptionalQDoubleSpinBox(parent=self)
        self._pre1SB.setToolTip("low E range (relative to e0) for pre-edge " "region")
        self._pre1SB.setValue(None)
        self._pre1SB.setContentsMargins(0, 0, 0, 0)
        self.layout().addRow(qt.QLabel("pre1", parent=self), self._pre1SB)
        # pre2
        self._pre2SB = _OptionalQDoubleSpinBox(parent=self)
        self._pre2SB.setToolTip("high E range (relative to e0) for pre-edge " "region")
        self._pre2SB.setValue(-50)
        self._pre2SB.setContentsMargins(0, 0, 0, 0)
        self.layout().addRow(qt.QLabel("pre2", parent=self), self._pre2SB)
        # norm1
        self._norm1SB = _OptionalQDoubleSpinBox(parent=self)
        self._norm1SB.setToolTip("low E range (relative to e0) for post-edge " "region")
        self._norm1SB.setContentsMargins(0, 0, 0, 0)
        self._norm1SB.setValue(100)
        self.layout().addRow(qt.QLabel("norm1", parent=self), self._norm1SB)
        # norm2
        self._norm2SB = _OptionalQDoubleSpinBox(parent=self)
        self._norm2SB.setToolTip(
            "high E range (relative to e0) for post-edge " "region"
        )
        self._norm2SB.setValue(None)
        self._norm2SB.setContentsMargins(0, 0, 0, 0)
        self.layout().addRow(qt.QLabel("norm2", parent=self), self._norm2SB)
        # order
        self._norm2SB.setToolTip(
            "order of the legendre polynomial for " "normalization"
        )
        self._orderSB = qt.QSpinBox(parent=self)
        self.layout().addRow(qt.QLabel("order", parent=self), self._orderSB)
        self._orderSB.setRange(0, 5)
        self._orderSB.setValue(3)
        # leexiang
        self._leexiangCB = qt.QCheckBox("", parent=self)
        self._leexiangCB.setToolTip(
            "boolean (default False)  to use the Lee & " "Xiang extension"
        )
        self.layout().addRow(qt.QLabel("leexiang", parent=self), self._leexiangCB)
        # tables
        self._tableCB = qt.QComboBox(parent=self)
        self._tableCB.setToolTip(
            'tabulated scattering factors: "chantler" '
            '(default) or "cl" (cromer-liberman)'
        )
        for item in ("chantler", "cl"):
            self._tableCB.addItem(item)
        index = self._tableCB.findText("chantler")
        assert index >= 0
        self._tableCB.setCurrentIndex(index)
        self.layout().addRow(qt.QLabel("tables", parent=self), self._tableCB)
        # fit erfc
        self._fiterfc = qt.QCheckBox(parent=self)
        self._fiterfc.setToolTip("fit parameters of error function " "(default False)")
        self.layout().addRow(qt.QLabel("fit erfc", parent=self), self._fiterfc)

        # expose API
        self.getPre1 = self._pre1SB.getValue
        self.setPre1 = self._pre1SB.setValue
        self.getPre2 = self._pre2SB.getValue
        self.setPre2 = self._pre2SB.setValue
        self.getNorm1 = self._norm1SB.getValue
        self.setNorm1 = self._norm1SB.setValue
        self.getNorm2 = self._norm2SB.getValue
        self.setNorm2 = self._norm2SB.setValue
        self.isUsingLeexiangExt = self._leexiangCB.isChecked
        self.setUsingLeexiangExt = self._leexiangCB.setChecked
        self.isFitParamErrFunc = self._fiterfc.isChecked
        self.setFitParamErrFunc = self._fiterfc.setChecked

        # connect signal / Slot
        self._atomicNumberSB.valueChanged.connect(self._valueChanged)
        self._edgeCB.currentIndexChanged.connect(self._valueChanged)
        self._e0SB.sigChanged.connect(self._valueChanged)
        self._pre1SB.sigChanged.connect(self._valueChanged)
        self._pre2SB.sigChanged.connect(self._valueChanged)
        self._norm1SB.sigChanged.connect(self._valueChanged)
        self._norm2SB.sigChanged.connect(self._valueChanged)
        self._orderSB.valueChanged.connect(self._valueChanged)
        self._leexiangCB.toggled.connect(self._valueChanged)
        self._tableCB.currentIndexChanged.connect(self._valueChanged)
        self._fiterfc.toggled.connect(self._valueChanged)

        # avoid several emission of the sigChanged signal
        self._lastParameters = None

    def _valueChanged(self, *arg, **kwargs):
        currentParameters = self.getParameters()
        if currentParameters != self._lastParameters:
            self._lastParameters = currentParameters
            self.sigChanged.emit()

    def getParameters(self):
        return {
            "z": self.getAtomicNumber(),
            "edge": self.getEdge(),
            "e0": self.getE0(),
            "pre1": self.getPre1(),
            "pre2": self.getPre2(),
            "norm1": self.getNorm1(),
            "norm2": self.getNorm2(),
            "order": self.getOrder(),
            "leexiang": self.isUsingLeexiangExt(),
            "tables": self.getTables(),
            "fit_erfc": self.isFitParamErrFunc(),
        }

    def setParameters(self, parameters):
        assert isinstance(parameters, dict)
        for key, value in parameters.items():
            if key == "z":
                self.setAtomicNumber(value)
            elif key == "edge":
                self.setEdge(value)
            elif key == "e0":
                self.setE0(value)
            elif key == "pre1":
                self.setPre1(value)
            elif key == "pre2":
                self.setPre2(value)
            elif key == "norm1":
                self.setNorm1(value)
            elif key == "norm2":
                self.setNorm2(value)
            elif key == "order":
                self.setOrder(value)
            elif key == "leexiang":
                self.setUsingLeexiangExt(value)
            elif key == "tables":
                self.setTables(value)
            elif key == "fit_erfc":
                self.setFitParamErrFunc(value)

    def getAtomicNumber(self):
        return self._atomicNumberSB.value()

    def setAtomicNumber(self, value):
        return self._atomicNumberSB.setValue(value)

    def getEdge(self):
        return self._edgeCB.currentText()

    def setEdge(self, edge):
        index = self._edgeCB.findText(edge)
        assert index >= 0
        self._edgeCB.setCurrentIndex(index)

    def getE0(self):
        return self._e0SB.getValue()

    def setE0(self, value):
        self._e0SB.setValue(value=value)

    def getOrder(self):
        return self._orderSB.value()

    def setOrder(self, order):
        self._orderSB.setValue(order)

    def getTables(self):
        return self._tableCB.currentText()

    def setTables(self, tables):
        index = self._tableCB.findText(tables)
        if index >= 0:
            self._tableCB.setCurrentIndex(index)


if __name__ == "__main__":
    app = qt.QApplication([])
    widget = _MBackParameters()
    widget.show()
    app.exec_()
