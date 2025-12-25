"""Tools to defining auto bk parameters"""

import logging

from silx.gui import qt

from .utils import _OptionalQDoubleSpinBox

_logger = logging.getLogger(__name__)


class _AutobkParameters(qt.QWidget):
    """
    Widget for setting the configuration of the larch 'autobk' process
    """

    sigChanged = qt.Signal()
    """Signal emitted when parameters changed"""
    # TODO: group it with the xftf windows
    _VALID_WINDOWS = ("kaiser", "hanning", "parzen", "welch", "gaussian", "sine")

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QFormLayout())
        # rbkg
        self._rbkgSB = qt.QDoubleSpinBox(parent=self)
        self._rbkgSB.setRange(0, 999999999)
        self._rbkgSB.setToolTip(
            "distance (in Ang) for chi(R) above which the " "signal is ignored"
        )
        self._rbkgSB.setValue(1)
        self.layout().addRow(qt.QLabel("rbkg"), self._rbkgSB)
        # e0
        self._e0SB = _OptionalQDoubleSpinBox(parent=self)
        self._e0SB.setToolTip(
            "edge energy, in eV.  If None, it will be " "determined here."
        )
        self._e0SB.setMinimum(0.0)
        self._e0SB.setValue(2000.0)
        self._e0SB.setValue(None)
        self.layout().addRow(qt.QLabel("e0", parent=self), self._e0SB)
        # edge step
        self._edgeStepSB = _OptionalQDoubleSpinBox(parent=self)
        self._edgeStepSB.setToolTip("edge step. If None, it will be determined.")
        self._edgeStepSB.setValue(None)
        self.layout().addRow(qt.QLabel("edge step", parent=self), self._edgeStepSB)
        # kmin
        self._kminSB = qt.QDoubleSpinBox(parent=self)
        self._kminSB.setRange(0, 999999999)
        self._kminSB.setToolTip("minimum k value.")
        self._kminSB.setValue(0)
        self.layout().addRow(qt.QLabel("spline kmin", parent=self), self._kminSB)
        # kmax
        self._kmaxSB = _OptionalQDoubleSpinBox(parent=self)
        self._kmaxSB.setToolTip(
            "maximum k value. If not provided will take the full range"
        )
        self._kmaxSB.setValue(20)
        self._kmaxSB.setValue(None)
        self.layout().addRow(qt.QLabel("spline kmax", parent=self), self._kmaxSB)
        # kweight
        # TODO: this should be included in the workflow process
        self._kweightSB = qt.QSpinBox(parent=self)
        self._kweightSB.setRange(0, 999999999)
        self._kweightSB.setToolTip("k weight")
        self._kweightSB.setValue(1)
        self.layout().addRow(qt.QLabel("spline k weight", parent=self), self._kweightSB)
        # dk
        self._dkSB = qt.QDoubleSpinBox(parent=self)
        self._dkSB.setRange(0, 999999999)
        self._dkSB.setValue(0.1)
        self._dkSB.setToolTip("FFT window parameter (dk)")
        self.layout().addRow(qt.QLabel("FFT window parameter", parent=self), self._dkSB)
        # window name
        self._windowCB = qt.QComboBox(parent=self)
        for winName in self._VALID_WINDOWS:
            self._windowCB.addItem(winName)
        index = self._windowCB.findText("hanning")
        assert index >= 0
        self._windowCB.setCurrentIndex(index)
        self.layout().addRow(qt.QLabel("fft window type", parent=self), self._windowCB)
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
        # nclamp
        self._nclampSB = qt.QSpinBox(parent=self)
        self._nclampSB.setValue(4)
        self._nclampSB.setToolTip("number of energy end-points for clamp")
        self.layout().addRow(qt.QLabel("n clamp", parent=self), self._nclampSB)
        # clamp_lo
        self._clampLoSB = qt.QSpinBox(parent=self)
        self._clampLoSB.setValue(1)
        self._clampLoSB.setToolTip("weight of low-energy clamp")
        self.layout().addRow(qt.QLabel("clamp low", parent=self), self._clampLoSB)
        # clamp_hi
        self._clampHiSB = qt.QSpinBox(parent=self)
        self._clampHiSB.setValue(1)
        self._clampHiSB.setToolTip("weight of high-energy clamp")
        self.layout().addRow(qt.QLabel("clamp high", parent=self), self._clampHiSB)
        # calc uncertainties
        self._calcUncertaintiesCB = qt.QCheckBox(parent=self)
        self._calcUncertaintiesCB.setChecked(True)
        self._calcUncertaintiesCB.setToolTip(
            "alculate uncertainties in " "mu_0(E) and chi(k)"
        )
        self.layout().addRow(
            qt.QLabel("calculate uncertainties", parent=self), self._calcUncertaintiesCB
        )
        # err sigma
        self._errSignalSB = qt.QSpinBox(parent=self)
        self._errSignalSB.setValue(1)
        self.layout().addRow(
            qt.QLabel("sigma uncertainties level", parent=self), self._errSignalSB
        )

        # expose API
        self.getRbkg = self._rbkgSB.value
        self.setRbkg = self._rbkgSB.setValue
        self.getE0 = self._e0SB.getValue
        self.setE0 = self._e0SB.setValue
        self.getEdgeStep = self._edgeStepSB.getValue
        self.setEdgeStep = self._edgeStepSB.setValue
        # self.getKNots = self._nknotsSB.getValue
        # self.setKNots = self._nknotsSB.setValue
        self.getKMin = self._kminSB.value
        self.setKMin = self._kminSB.setValue
        self.getKMax = self._kmaxSB.getValue
        self.setKMax = self._kmaxSB.setValue
        self.getKWeight = self._kweightSB.value
        self.setKWeight = self._kweightSB.setValue
        self.getDk = self._dkSB.value
        self.setDk = self._dkSB.setValue
        self.getWindow = self._windowCB.currentText
        self.setWindow = self.setWindow
        self.getNfft = self._nfftSB.value
        self.setNfft = self._nfftSB.setValue
        self.getKStep = self._kstepSB.value
        self.setKStep = self._kstepSB.setValue
        self.getNClamp = self._nclampSB.value
        self.setNClamp = self._nclampSB.setValue
        self.getClampLow = self._clampLoSB.value
        self.setClampLow = self._clampLoSB.setValue
        self.getClampHigh = self._clampHiSB.value
        self.setClampHigh = self._clampHiSB.setValue
        self.isCalcUncertainties = self._calcUncertaintiesCB.isChecked
        self.setCalcUncertainties = self._calcUncertaintiesCB.setChecked
        self.getSigmaErr = self._errSignalSB.value
        self.setSigmaErr = self._errSignalSB.setValue

        # connect signal / slots
        self._rbkgSB.valueChanged.connect(self._valueChanged)
        self._e0SB.sigChanged.connect(self._valueChanged)
        self._edgeStepSB.sigChanged.connect(self._valueChanged)
        # self._nknotsSB.sigChanged.connect(self._parametersChanged)
        self._kminSB.valueChanged.connect(self._valueChanged)
        self._kmaxSB.sigChanged.connect(self._valueChanged)
        self._kweightSB.valueChanged.connect(self._valueChanged)
        self._dkSB.valueChanged.connect(self._valueChanged)
        self._windowCB.currentTextChanged.connect(self._valueChanged)
        self._nfftSB.valueChanged.connect(self._valueChanged)
        self._kstepSB.valueChanged.connect(self._valueChanged)
        self._nclampSB.valueChanged.connect(self._valueChanged)
        self._clampLoSB.valueChanged.connect(self._valueChanged)
        self._clampHiSB.valueChanged.connect(self._valueChanged)
        self._calcUncertaintiesCB.toggled.connect(self._valueChanged)
        self._errSignalSB.valueChanged.connect(self._valueChanged)

        # avoid several emission of the sigChanged signal
        self._lastParameters = None

    def getParameters(self):
        return {
            "rbkg": self.getRbkg(),
            "e0": self.getE0(),
            "edge_step": self.getEdgeStep(),
            # 'nknots': self.getKNots(),
            "kmin": self.getKMin(),
            "kmax": self.getKMax(),
            "kweight": self.getKWeight(),
            "dk": self.getDk(),
            "win": self.getWindow(),
            "nfft": self.getNfft(),
            "kstep": self.getKStep(),
            "nclamp": self.getNClamp(),
            "clamp_lo": self.getClampLow(),
            "clamp_hi": self.getClampHigh(),
            "calc_uncertaintites": self.isCalcUncertainties(),
            "err_sigma": self.getSigmaErr(),
        }

    def setParameters(self, parameters):
        assert isinstance(parameters, dict)
        for key, value in parameters.items():
            if key == "rbkg":
                self.setRbkg(value)
            elif key == "e0":
                self.setE0(value)
            elif key == "edge_step":
                self.setEdgeStep(value)
            elif key == "knots":
                self.setKNots(value)
            elif key == "kmin":
                self.setKMin(value)
            elif key == "kmax":
                self.setKMax(value)
            elif key == "kweight":
                self.setKWeight(value)
            elif key == "dk":
                self.setDk(value)
            elif key == "win":
                self.setWindow(value)
            elif key == "nfft":
                self.setNfft(value)
            elif key == "kstep":
                self.setKStep(value)
            elif key == "nclamp":
                self.setNClamp(value)
            elif key == "clamp_lo":
                self.setClampLow(value)
            elif key == "clamp_hi":
                self.setClampHigh(value)
            elif key == "calc_uncertaintites":
                self.setCalcUncertainties(value)
            elif key == "err_sigma":
                self.setSigmaErr(value)

    def setWindow(self, window):
        assert window in self._VALID_WINDOWS
        index = self._windowCB.findText(window)
        if index >= 0:
            self._windowCB.setCurrentIndex(index)
        else:
            _logger.warning(window + " not found.")

    def _valueChanged(self, *args, **kwargs):
        currentParameters = self.getParameters()
        if currentParameters != self._lastParameters:
            self._lastParameters = currentParameters
            self.sigChanged.emit()
