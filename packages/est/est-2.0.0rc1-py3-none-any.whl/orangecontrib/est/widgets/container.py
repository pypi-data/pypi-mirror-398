from silx.gui import qt


class _ParameterWindowContainer(qt.QWidget):
    """Embed the larch parameters windows (should contains getParameters and
    setParameters and have a sigChanged signal) and add it a 'manual' update
    mode for convenience
    """

    sigChanged = qt.Signal()
    """Signal emitted when some computation is required"""

    def __init__(self, parent, parametersWindow):
        assert parametersWindow is not None
        super().__init__(parent=parent)
        self.setLayout(qt.QGridLayout())
        self._mainwidget = parametersWindow(parent=self)
        assert hasattr(self._mainwidget, "setParameters")
        assert hasattr(self._mainwidget, "getParameters")
        self.layout().addWidget(self._mainwidget, 0, 0, 1, 3)
        self._autoCB = qt.QCheckBox("manual update", parent=self)
        self.layout().addWidget(self._autoCB, 1, 1, 1, 1)
        self._autoCB.setToolTip(
            "if activated will wait until you press the "
            '"update" button to launch processing. '
            "Otherwise executed for each modification in "
            "the paramters"
        )
        self._manualUpdatePB = qt.QPushButton("update")
        self.layout().addWidget(self._manualUpdatePB, 1, 2, 1, 1)

        # setup
        self._manualUpdatePB.setVisible(False)

        # connect signal / slot
        self._autoCB.toggled.connect(self._manualUpdatePB.setVisible)
        self._manualUpdatePB.pressed.connect(self._update)

        if hasattr(self._mainwidget, "sigChanged"):
            # manage larch windows
            _sig = self._mainwidget.sigChanged
        elif hasattr(self._mainwidget, "sigFTParametersSignal"):
            _sig = self._mainwidget.sigFTParametersSignal
        elif hasattr(self._mainwidget, "sigNormalizationParametersSignal"):
            _sig = self._mainwidget.sigNormalizationParametersSignal
        elif hasattr(self._mainwidget, "sigXASNormalizationParametersSignal"):
            _sig = self._mainwidget.sigXASNormalizationParametersSignal
        elif hasattr(self._mainwidget, "sigPostEdgeParametersSignal"):
            _sig = self._mainwidget.sigPostEdgeParametersSignal
        else:
            raise ValueError("window not recognized")

        _sig.connect(self._filteredUpdate)

    def _filteredUpdate(self, *args, **kwargs):
        """call _update only if in automatic update mode"""
        if not self._autoCB.isChecked():
            self._update()

    def _update(self, *args, **kwargs):
        self.sigChanged.emit()

    def getParameters(self):
        return self._mainwidget.getParameters()

    def setParameters(self, params):
        self._mainwidget.setParameters(params)
