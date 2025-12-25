from typing import Optional
from typing import Union

from ewoksorange.gui.orange_utils.orange_imports import gui
from ewoksorange.gui.owwidgets.threaded import OWEwoksWidgetOneThread
from silx.gui import qt

from est.core.io._utils.ascii import split_ascii_url
from est.core.io._utils.load import get_input_type
from est.core.io.information import InputInformation
from est.core.process.read import ReadXasObject
from est.core.types.data import InputType
from est.core.types.xasobject import XASObject
from est.gui.xas_object_definition.window import XASObjectWindow


class XASInputOW(OWEwoksWidgetOneThread, ewokstaskclass=ReadXasObject):
    """
    Widget used for signal extraction
    """

    name = "xas input"
    description = "Read .dat file and convert it to spectra"
    icon = "icons/input.png"
    priority = 0
    keywords = ["spectroscopy", "signal", "input", "file"]

    want_main_area = True
    resizing_enabled = True
    want_control_area = False

    def __init__(self):
        super().__init__()
        self._inputWindow = qt.QWidget(parent=self)
        self._inputWindow.setLayout(qt.QGridLayout())

        self._inputDialog = XASObjectWindow(parent=self)
        self._inputWindow.layout().addWidget(self._inputDialog, 0, 0, 1, 2)

        # add the apply button
        types = qt.QDialogButtonBox.Ok
        self._buttons = qt.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        self.layout().addWidget(self._buttons)

        spacer = qt.QWidget(parent=self)
        spacer.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        self._inputWindow.layout().addWidget(spacer, 2, 0)

        layout = gui.vBox(self.mainArea, "input").layout()
        layout.addWidget(self._inputWindow)

        self.loadSettings(
            input_information=self.get_task_input_value(
                "input_information", default=None
            ),
        )

        # expose api
        self.apply = self.execute_ewoks_task

        # signal / slot connection
        self._buttons.accepted.connect(self.hide)
        self._buttons.accepted.connect(self.execute_ewoks_task)
        self._inputDialog.getMainWindow().editingFinished.connect(self._storeSettings)

    def setFileSelected(self, file_path):
        self._inputDialog.setAsciiFile(file_path)

    def loadSettings(self, input_information: Union[InputInformation, dict, None]):
        if input_information is None:
            return
        if isinstance(input_information, dict):
            input_information = InputInformation.from_dict(input_information)

        data_url = (
            input_information.spectra_url
            or input_information.channel_url
            or input_information.mu_ref_url
        )
        input_type = get_input_type(data_url)

        if input_type is InputType.hdf5_spectra:
            if input_information.spectra_url is not None:
                self._inputDialog.setSpectraUrl(input_information.spectra_url)
            if input_information.channel_url is not None:
                self._inputDialog.setEnergyUrl(input_information.channel_url)
            if input_information.mu_ref_url is not None:
                self._inputDialog.setMuRefUrl(input_information.mu_ref_url)
            self._inputDialog.getMainWindow().setSkipConcatenatedNPoints(
                input_information.trim_concatenated_n_points
            )
            self._inputDialog.getMainWindow().setSkipConcatenatedNSpectra(
                input_information.skip_concatenated_n_spectra
            )
            self._inputDialog.getMainWindow().setConcatenatedSpectraSectionSize(
                input_information.concatenated_spectra_section_size
            )
            self._inputDialog.getMainWindow().setConcatenatedSpectra(
                input_information.is_concatenated
            )
        elif input_type is InputType.ascii_spectrum:
            input_type = InputType.ascii_spectrum
            self._inputDialog.setAsciiFile(input_information.spectra_url.file_path())
            # TODO: check if there is any scan title in here
            urls_with_col_names = {
                self._inputDialog.setEnergyColName: input_information.channel_url,
                self._inputDialog.setAbsColName: input_information.spectra_url,
                self._inputDialog.setMonitorColName: input_information.mu_ref_url,
            }
            for setter, value in urls_with_col_names.items():
                if value is not None:
                    setter(split_ascii_url(value).col_name)
            scan_title = split_ascii_url(input_information.spectra_url).scan_title
            if scan_title is not None:
                self._inputDialog.setScanTitle(scan_title)
        elif input_type is not None:
            raise ValueError(f"Unxpected inpit type {input_type}")

        if len(input_information.dimensions) == 3:
            self._inputDialog.setDimensions(input_information.dimensions)
        elif not len(input_information.dimensions) == 0:
            raise ValueError("spectra dimensions are expected to be 3D")
        self._inputDialog.setEnergyUnit(input_information.energy_unit)

        self._inputDialog.getMainWindow().setMinLog(input_information.min_log)

        self._inputDialog.setCurrentType(input_type)

    def _storeSettings(self):
        self.update_default_inputs(
            input_information=self._inputDialog.getInputInformation().to_dict()
        )

    def sizeHint(self):
        return qt.QSize(400, 200)

    def buildXASObj(self) -> Optional[XASObject]:
        return self._inputDialog.buildXASObject()
