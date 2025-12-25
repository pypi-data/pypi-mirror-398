from AnyQt import QtWidgets
from ewoksorange.gui.orange_utils.orange_imports import gui

from est.core.process.noise import NoiseProcess
from est.gui.noise import SavitskyGolayNoise
from est.gui.noise import SavitskyGolayNoiseOpts

from ...base import EstProcessWidget


class NoiseOW(EstProcessWidget, ewokstaskclass=NoiseProcess):
    """
    Widget used to make the selection of a region of Interest to treat in a
    Dataset.
    """

    name = "noise"
    description = "Compute noise using Savitsky-Golay"
    icon = "icons/noise.svg"
    priority = 40
    keywords = ["dataset", "data", "noise"]

    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self._window = SavitskyGolayNoise(parent=self)
        layout = gui.vBox(self.mainArea, "noise").layout()
        layout.addWidget(self._window)

        # buttons
        types = QtWidgets.QDialogButtonBox.Ok
        self._buttons = QtWidgets.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        layout.addWidget(self._buttons)
        self._buttons.hide()

        # initial parameters
        parameters = self.get_default_input_values()
        parameters.setdefault("e_min", SavitskyGolayNoiseOpts.DEFAULT_E_START)
        parameters.setdefault("e_max", SavitskyGolayNoiseOpts.DEFAULT_E_STOP)
        self._window.setParameters(parameters)

        # signal / slot connection
        self._window.sigChanged.connect(self._updateProcess)

    def _updateProcess(self):
        self.update_default_inputs(**self._window.getParameters())
        self.handleNewSignals()
