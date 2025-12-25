from silx.gui import qt

from .utils import _OptionalQDoubleSpinBox
from .utils import _OptionalQIntSpinBox


class _MPreEdgeParameters(qt.QWidget):
    """
    Widget for setting the configuration of the larch 'pre edge' process
    """

    sigChanged = qt.Signal()
    """Signal emitted when parameters changed"""

    sigE0CalculatorRequest = qt.Signal()
    """Signal emitted when E0 calculator is requested"""

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QGridLayout())

        # e0
        self._e0SB = _OptionalQDoubleSpinBox(parent=self)
        self._e0SB.setToolTip(
            "edge energy, in eV.  If None, it will be " "determined here."
        )
        self._e0SB.setMinimum(0.0)
        self._e0SB.setValue(2000.0)
        self._e0SB.setValue(None)
        self.layout().addWidget(qt.QLabel("e0", parent=self), 0, 0)
        self.layout().addWidget(self._e0SB, 0, 1)

        # step
        self._stepSP = _OptionalQDoubleSpinBox(parent=self)
        self._stepSP.setToolTip("edge jump. If None, it will be determined")
        self._stepSP.setValue(None)
        self.layout().addWidget(qt.QLabel("step", parent=self), 1, 0)
        self.layout().addWidget(self._stepSP, 1, 1)
        # pre1
        self._pre1SB = _OptionalQDoubleSpinBox(parent=self)
        self._pre1SB.setToolTip("low E range (relative to e0) for pre-edge " "region")
        self._pre1SB.setValue(None)
        self._pre1SB.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(qt.QLabel("pre1", parent=self), 2, 0)
        self.layout().addWidget(self._pre1SB, 2, 1)
        # pre2
        self._pre2SB = qt.QDoubleSpinBox(parent=self)
        self._pre2SB.setToolTip("high E range (relative to e0) for pre-edge " "region")
        self._pre2SB.setMinimum(-99999)
        self._pre2SB.setMaximum(99999)
        self._pre2SB.setValue(-50)
        self._pre2SB.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(qt.QLabel("pre2", parent=self), 3, 0)
        self.layout().addWidget(self._pre2SB, 3, 1)
        # norm1
        self._norm1SB = qt.QDoubleSpinBox(parent=self)
        self._norm1SB.setToolTip("low E range (relative to e0) for post-edge " "region")
        self._norm1SB.setContentsMargins(0, 0, 0, 0)
        self._norm1SB.setMinimum(-99999)
        self._norm1SB.setMaximum(99999)
        self._norm1SB.setValue(100)
        self.layout().addWidget(qt.QLabel("norm1", parent=self), 4, 0)
        self.layout().addWidget(self._norm1SB, 4, 1)
        # norm2
        self._norm2SB = _OptionalQDoubleSpinBox(parent=self)
        self._norm2SB.setToolTip(
            "high E range (relative to e0) for post-edge " "region"
        )
        self._norm2SB.setValue(None)
        self._norm2SB.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(qt.QLabel("norm2", parent=self), 5, 0)
        self.layout().addWidget(self._norm2SB, 5, 1)
        # nvict
        self._nvictSB = qt.QSpinBox(parent=self)
        self._nvictSB.setValue(0)
        self.layout().addWidget(qt.QLabel("nvict (energy exponent)", parent=self), 6, 0)
        self.layout().addWidget(self._nvictSB, 6, 1)
        # nnorm
        self._nnorm = _OptionalQIntSpinBox(parent=self)
        self._nnorm.setRange(0, 3)
        self._nnorm.setValue(None)
        self._nnorm.setToolTip(
            "degree of polynomial (ie, nnorm+1 coefficients "
            "will be found) for post-edge normalization "
            "curve. If unset nnorm will default to 2 in "
            "norm2-norm1>400, to 1 if 100>norm2-norm1>300, "
            "and to 0 in norm2-norm1<100."
        )
        self.layout().addWidget(qt.QLabel("polynomial degree", parent=self), 7, 0)
        self.layout().addWidget(self._nnorm, 7, 1)
        # make_flat
        self._makeFlatCB = qt.QCheckBox("", parent=self)
        self._makeFlatCB.setToolTip("to calculate flattened output")
        self._makeFlatCB.setChecked(True)
        self.layout().addWidget(qt.QLabel("make flat", parent=self), 8, 0)
        self.layout().addWidget(self._makeFlatCB, 8, 1)
        # emin_area
        self._eminAreaSB = _OptionalQDoubleSpinBox(parent=self)
        self._eminAreaSB.setMinimum(0.0)
        self._eminAreaSB.setValue(None)
        self._eminAreaSB.setToolTip(
            "Energy threshold for area normalization."
            "norm_area will be estimated so that the "
            "area between emin_area and norm2 is equal "
            "to (norm2-emin_area). By default emin_area"
            " will be set to the *nominal* edge energy "
            "for the element and "
            "edge - 3*core_level_width"
        )
        self.layout().addWidget(qt.QLabel("e min area", parent=self), 9, 0)
        self.layout().addWidget(self._eminAreaSB, 9, 1)

        # expose API
        self.getStep = self._stepSP.getValue
        self.setStep = self._stepSP.setValue
        self.getPre1 = self._pre1SB.getValue
        self.setPre1 = self._pre1SB.setValue
        self.getPre2 = self._pre2SB.value
        self.setPre2 = self._pre2SB.setValue
        self.getNorm1 = self._norm1SB.value
        self.setNorm1 = self._norm1SB.setValue
        self.getNorm2 = self._norm2SB.getValue
        self.setNorm2 = self._norm2SB.setValue
        self.getNNorm = self._nnorm.getValue
        self.setNNorm = self._nnorm.setValue
        self.getNVict = self._nvictSB.value
        self.setNVict = self._nvictSB.setValue
        self.isUsingMakeFlat = self._makeFlatCB.isChecked
        self.setMakeFlat = self._makeFlatCB.setChecked
        self.getEMinArea = self._eminAreaSB.getValue
        self.setEMinArea = self._eminAreaSB.setValue

        # connect signal / Slot
        self._stepSP.sigChanged.connect(self._valueChanged)
        self._e0SB.sigChanged.connect(self._valueChanged)
        self._pre1SB.sigChanged.connect(self._valueChanged)
        self._pre2SB.editingFinished.connect(self._valueChanged)
        self._norm1SB.editingFinished.connect(self._valueChanged)
        self._norm2SB.sigChanged.connect(self._valueChanged)
        self._nnorm.sigChanged.connect(self._valueChanged)
        self._nvictSB.editingFinished.connect(self._valueChanged)
        self._makeFlatCB.toggled.connect(self._valueChanged)
        self._eminAreaSB.sigChanged.connect(self._valueChanged)

        # avoid several emission of the sigChanged signal
        self._lastParameters = None

    def _valueChanged(self, *arg, **kwargs):
        current_values = self.getParameters()
        if current_values != self._lastParameters:
            self._lastParameters = current_values
            self.sigChanged.emit()

    def getParameters(self):
        return {
            "e0": self.getE0(),
            "step": self.getStep(),
            "pre1": self.getPre1(),
            "pre2": self.getPre2(),
            "norm1": self.getNorm1(),
            "norm2": self.getNorm2(),
            "nnorm": self.getNNorm(),
            "nvict": self.getNVict(),
            "make_flat": self.isUsingMakeFlat(),
            "emin_area": self.getEMinArea(),
        }

    def setParameters(self, parameters):
        assert isinstance(parameters, dict)
        for key, value in parameters.items():
            if key == "step":
                self.setStep(value)
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
            elif key == "nnorm":
                self.setNNorm(value)
            elif key == "nvict":
                self.setNVict(value)
            elif key == "make_flat":
                self.setMakeFlat(value)
            elif key == "emin_area":
                self.setEMinArea(value)

    def getE0(self):
        return self._e0SB.getValue()

    def setE0(self, value):
        self._e0SB.setValue(value=value)

    def _updateE0FromDialog(self):
        self.sigE0CalculatorRequest.emit()
