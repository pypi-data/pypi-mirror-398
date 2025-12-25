from typing import Optional

from silx.gui import qt
from silx.io.url import DataUrl

from ...core.io.information import InputInformation
from ...core.io.read_xas import build_ascii_data_url
from ...core.io.read_xas import read_from_input_information
from ...core.types.data import InputType
from ...core.types.xasobject import XASObject
from .ascii import XASObjectFromAscii
from .hdf5 import XASObjectFromH5


class _InputTypeWidget(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QHBoxLayout())
        self.layout().addWidget(qt.QLabel("input type:"))
        self._inputTypeCB = qt.QComboBox(parent=self)
        for input_type in InputType:
            self._inputTypeCB.addItem(input_type.value)
        self.layout().addWidget(self._inputTypeCB)

        # expose API
        self.currentChanged = self._inputTypeCB.currentIndexChanged

    def getInputType(self):
        """Return the current input type"""
        return InputType(self._inputTypeCB.currentText())

    def setInputType(self, input_type):
        _input_type = InputType(input_type)
        idx = self._inputTypeCB.findText(_input_type.value)
        assert idx >= 0
        self._inputTypeCB.setCurrentIndex(idx)


class XASObjectDialog(qt.QWidget):
    """
    Interface used to select inputs for defining a XASObject
    """

    editingFinished = qt.Signal()

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        layout = qt.QGridLayout()
        self.setLayout(layout)

        self._inputType = _InputTypeWidget(parent=self)
        self.layout().addWidget(self._inputType, 0, 0)
        spacer = qt.QWidget(parent=self)
        spacer.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        layout.addWidget(spacer, 0, 1)

        # single ASCII file (.csv, .xmu, .dat, .spec)
        self._asciiDialog = XASObjectFromAscii(parent=self)
        self.layout().addWidget(self._asciiDialog, 1, 0, 1, 2)

        # .h5 file
        self._h5Dialog = XASObjectFromH5(parent=self)
        self.layout().addWidget(self._h5Dialog, 2, 0, 1, 2)

        spacer = qt.QWidget(parent=self)
        spacer.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        self.layout().addWidget(spacer, 99, 0)

        # connect signal / slot
        self._inputType.currentChanged.connect(self._updateWidgetVisibility)
        self._inputType.currentChanged.connect(self._editingIsFinished)

        self._asciiDialog.editingFinished.connect(self._editingIsFinished)
        self._h5Dialog.editingFinished.connect(self._editingIsFinished)

        # set default read mode to hdf5
        self.setCurrentType(InputType.hdf5_spectra)
        # default setting
        self._updateWidgetVisibility()

    def _updateWidgetVisibility(self):
        self._asciiDialog.setVisible(
            self._inputType.getInputType() == InputType.ascii_spectrum
        )
        self._h5Dialog.setVisible(
            self._inputType.getInputType() == InputType.hdf5_spectra
        )

    def buildXASObject(self) -> Optional[XASObject]:
        input_information = self.getInputInformation()

        spectra_url = input_information.spectra_url
        energy_url = input_information.channel_url

        if spectra_url in (None, "") or energy_url in (None, ""):
            return None

        return read_from_input_information(input_information)

    def _editingIsFinished(self, *args, **kwargs):
        self.editingFinished.emit()

    # getter / setter exposed

    def getCurrentType(self):
        return self._inputType.getInputType()

    def setCurrentType(self, input_type):
        self._inputType.setInputType(input_type=input_type)

    def getEnergyColName(self):
        return self._asciiDialog.getEnergyColName()

    def setEnergyColName(self, name):
        self._asciiDialog.setEnergyColName(name=name)

    def getAbsColName(self):
        return self._asciiDialog.getAbsColName()

    def setAbsColName(self, name):
        self._asciiDialog.setAbsColName(name=name)

    def getMonitorColName(self):
        return self._asciiDialog.getMonitorColName()

    def setMonitorColName(self, name):
        self._asciiDialog.setMonitorColName(name=name)

    def getScanTitle(self):
        return self._asciiDialog.getScanTitle()

    def setScanTitle(self, scan_title):
        self._asciiDialog.setScanTitle(scan_title=scan_title)

    def getAsciiFile(self):
        return self._asciiDialog.getFileSelected()

    def setAsciiFile(self, file_path):
        self._asciiDialog.setFileSelected(file_path=file_path)

    def getSpectraUrl(self) -> Optional[DataUrl]:
        if self.getCurrentType() is InputType.hdf5_spectra:
            return self._h5Dialog.getSpectraUrl()
        else:
            return build_ascii_data_url(
                file_path=self.getAsciiFile(),
                col_name=self.getAbsColName(),
                scan_title=self.getScanTitle(),
            )

    def setSpectraUrl(self, url):
        self._h5Dialog.setSpectraUrl(url=url)

    def getMuRefUrl(self):
        # Same use getMuRefUrl but does not normalize spectra when loading
        if self.getCurrentType() is InputType.hdf5_spectra:
            return self._h5Dialog.getMuRefUrl()
        else:
            col_name = self.getMonitorColName()
            if col_name:
                return build_ascii_data_url(
                    file_path=self.getAsciiFile(),
                    col_name=col_name,
                    scan_title=self.getScanTitle(),
                )

    def setMuRefUrl(self, url):
        self._h5Dialog.setMuRefUrl(url=url)

    def getEnergyUrl(self) -> Optional[DataUrl]:
        if self.getCurrentType() is InputType.hdf5_spectra:
            return self._h5Dialog.getEnergyUrl()
        else:
            return build_ascii_data_url(
                file_path=self.getAsciiFile(),
                col_name=self.getEnergyColName(),
                scan_title=self.getScanTitle(),
            )

    def setEnergyUrl(self, url):
        self._h5Dialog.setEnergyUrl(url=url)

    def getEnergyUnit(self):
        return self._currentDialog.getEnergyUnit()

    def setEnergyUnit(self, unit):
        for dialog in self._allDialogs:
            dialog.setEnergyUnit(unit=unit)

    def getConfigurationUrl(self):
        return self._h5Dialog.getConfigurationUrl()

    def setConfigurationUrl(self, url):
        self._h5Dialog.setConfigurationUrl(url=url)

    def getDimensions(self):
        return self._h5Dialog.getDimensions()

    def setDimensions(self, dims):
        self._h5Dialog.setDimensions(dims=dims)

    def getInputInformation(self):
        return InputInformation(
            spectra_url=self.getSpectraUrl(),
            channel_url=self.getEnergyUrl(),
            dimensions=self.getDimensions(),
            energy_unit=self.getEnergyUnit(),
            mu_ref_url=self.getMuRefUrl(),
            min_log=self.getMinLog(),
            is_concatenated=self._h5Dialog.isSpectraConcatenated(),
            trim_concatenated_n_points=self._h5Dialog.getSkipConcatenatedNPoints(),
            skip_concatenated_n_spectra=self._h5Dialog.getSkipConcatenatedNSpectra(),
            concatenated_spectra_section_size=self._h5Dialog.getConcatenatedSpectraSectionSize(),
        )

    def setConcatenatedSpectra(self, value: bool):
        self._h5Dialog.setConcatenatedSpectra(value)

    def setSkipConcatenatedNPoints(self, value: int):
        self._h5Dialog.setSkipConcatenatedNPoints(value)

    def setSkipConcatenatedNSpectra(self, value: int):
        self._h5Dialog.setSkipConcatenatedNSpectra(value)

    def setConcatenatedSpectraSectionSize(self, value: int):
        self._h5Dialog.setConcatenatedSpectraSectionSize(value)

    def getMinLog(self) -> bool:
        return self._currentDialog.getMinLog()

    def setMinLog(self, value: bool) -> None:
        self._currentDialog.setMinLog(value)

    @property
    def _currentDialog(self):
        # TODO: FIXME: design should be improve to avoid those kind of conditions
        if self.getCurrentType() == InputType.hdf5_spectra:
            return self._h5Dialog
        else:
            return self._asciiDialog

    @property
    def _allDialogs(self):
        return [self._h5Dialog, self._asciiDialog]
