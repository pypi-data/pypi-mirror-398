from silx.gui import qt

from .utils import _OptionalQDoubleSpinBox


class _MXFTFParameters(qt.QWidget):
    """
    Widget for setting the configuration of the larch 'xftf' process
    """

    sigChanged = qt.Signal()
    """Signal emitted when parameters changed"""

    _VALID_WINDOWS = ("kaiser", "hanning", "parzen", "welch", "gaussian", "sine")

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QFormLayout())

        # kmin
        self._kminSB = qt.QDoubleSpinBox(parent=self)
        self._kminSB.setSingleStep(1.0)
        self._kminSB.setValue(0)
        self._kminSB.setRange(0, 1000)
        self._kminSB.setToolTip("starting k for FT Window")
        self.layout().addRow(qt.QLabel("k min", parent=self), self._kminSB)
        # kmax
        self._kmaxSB = _OptionalQDoubleSpinBox(parent=self)
        self._kmaxSB.setRange(0, 2000)
        self._kmaxSB.setSingleStep(1.0)
        self._kmaxSB.setValue(20)
        self._kmaxSB.setValue(None)
        self._kmaxSB.setToolTip(
            "ending k for FT Window. If none provided then will take the 90% of k"
        )
        self.layout().addRow(qt.QLabel("k max", parent=self), self._kmaxSB)
        # kweight
        self._kWeightSB = qt.QSpinBox(parent=self)
        self._kWeightSB.setValue(0)
        self._kWeightSB.setToolTip("exponent for weighting spectra by " "k**kweight")
        self.layout().addRow(qt.QLabel("k weight", parent=self), self._kWeightSB)
        # dk1
        self._dk1SB = qt.QDoubleSpinBox(parent=self)
        self._dk1SB.setRange(0, 10000)
        self._dk1SB.setValue(1)
        self._dk1SB.setSingleStep(1.0)
        self._dk1SB.setToolTip("tapering parameter for FT Window")
        self.layout().addRow(qt.QLabel("dk", parent=self), self._dk1SB)
        # dk2
        self._dk2SB = _OptionalQDoubleSpinBox(parent=self)
        self._dk2SB.setRange(0, 10000)
        self._dk2SB.setSingleStep(1.0)
        self._dk2SB.setValue(None)
        self._dk2SB.setToolTip("second tapering parameter for FT Window")
        self.layout().addRow(qt.QLabel("dk2", parent=self), self._dk2SB)
        # with phase
        self._withPhaseCB = qt.QCheckBox(parent=self)
        self._withPhaseCB.setChecked(False)
        self._withPhaseCB.setToolTip(
            "output the phase as well as magnitude, " "real, imag"
        )
        self.layout().addRow(qt.QLabel("phase", parent=self), self._withPhaseCB)
        # window
        self._windowCB = qt.QComboBox(parent=self)
        for winName in self._VALID_WINDOWS:
            self._windowCB.addItem(winName)
        index = self._windowCB.findText("kaiser")
        assert index >= 0
        self._windowCB.setCurrentIndex(index)
        self.layout().addRow(qt.QLabel("window", parent=self), self._windowCB)
        # rmax_out
        self._rmax_outSB = qt.QDoubleSpinBox(parent=self)
        self._rmax_outSB.setValue(10.0)
        self._rmax_outSB.setRange(0, 999999)
        self._rmax_outSB.setToolTip("highest R for output data")
        self.layout().addRow(
            qt.QLabel("highest R (Ang)", parent=self), self._rmax_outSB
        )
        # nfft
        self._nfftSB = qt.QSpinBox(parent=self)
        self._nfftSB.setMaximum(999999)
        self._nfftSB.setValue(2048)
        self._nfftSB.setToolTip("value to use for N_fft")
        self.layout().addRow(qt.QLabel("N fft", parent=self), self._nfftSB)
        # kstep
        self._kstepSB = qt.QDoubleSpinBox(parent=self)
        self._kstepSB.setToolTip("value to use for delta_k")
        self._kstepSB.setValue(0.05)
        self._kstepSB.setSingleStep(0.05)
        self.layout().addRow(qt.QLabel("k step", parent=self), self._kstepSB)

        # expose API
        self.getKMin = self._kminSB.value
        self.setKMin = self._kminSB.setValue
        self.getKMax = self._kmaxSB.getValue
        self.setKMax = self._kmaxSB.setValue
        self.getKWeight = self._kWeightSB.value
        self.setKWeight = self._kWeightSB.setValue
        self.setDK1 = self._dk1SB.setValue
        self.getDK1 = self._dk1SB.value
        self.setDK2 = self._dk2SB.setValue
        self.getDK2 = self._dk2SB.getValue
        self.isUsingPhase = self._withPhaseCB.isChecked
        self.setUsingPhase = self._withPhaseCB.setChecked
        self.getWindow = self._windowCB.currentText
        self.setRMaxOut = self._rmax_outSB.setValue
        self.getRMaxOut = self._rmax_outSB.value
        self.getNfft = self._nfftSB.value
        self.setNfft = self._nfftSB.setValue
        self.getKStep = self._kstepSB.value
        self.setKStep = self._kstepSB.setValue

        # connect signal / Slot
        self._kminSB.valueChanged.connect(self._valueChanged)
        self._kmaxSB.sigChanged.connect(self._valueChanged)
        self._kWeightSB.valueChanged.connect(self._valueChanged)
        self._dk1SB.valueChanged.connect(self._valueChanged)
        self._dk2SB.sigChanged.connect(self._valueChanged)
        self._withPhaseCB.toggled.connect(self._valueChanged)
        self._windowCB.currentIndexChanged.connect(self._valueChanged)
        self._rmax_outSB.valueChanged.connect(self._valueChanged)
        self._nfftSB.valueChanged.connect(self._valueChanged)
        self._kstepSB.valueChanged.connect(self._valueChanged)

        # avoid several emission of the sigChanged signal
        self._lastParameters = None

    def setWindow(self, window):
        assert window in self._VALID_WINDOWS
        index = self._windowCB.findText(window)
        assert index >= 0
        self._windowCB.setCurrentIndex(index)

    def _valueChanged(self, *arg, **kwargs):
        currentParameters = self.getParameters()
        if currentParameters != self._lastParameters:
            self._lastParameters = currentParameters
            self.sigChanged.emit()

    def getParameters(self):
        return {
            "kmin": self.getKMin(),
            "kmax": self.getKMax(),
            "kweight": self.getKWeight(),
            "dk": self.getDK1(),
            "dk2": self.getDK2(),
            "with_phase": self.isUsingPhase(),
            "window": self.getWindow(),
            "rmax_out": self.getRMaxOut(),
            "nfft": self.getNfft(),
            "kstep": self.getKStep(),
        }

    def setParameters(self, parameters):
        assert isinstance(parameters, dict)
        for key, value in parameters.items():
            if key == "kmin":
                self.setKMin(value)
            elif key == "kmax":
                self.setKMax(value)
            elif key == "kweight":
                self.setKWeight(value)
            elif key == "dk":
                self.setDK1(value)
            elif key == "dk2":
                self.setDK2(value)
            elif key == "with_phase":
                self.setUsingPhase(value)
            elif key == "window":
                self.setWindow(value)
            elif key == "rmax_out":
                self.setRMaxOut(value)
            elif key == "nfft":
                self.setNfft(value)
            elif key == "kstep":
                self.setKStep(value)


if __name__ == "__main__":
    app = qt.QApplication([])
    widget = _MXFTFParameters()
    widget.show()
    app.exec_()
