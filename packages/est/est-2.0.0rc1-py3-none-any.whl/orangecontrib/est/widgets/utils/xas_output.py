import logging

import h5py
from ewoksorange.gui.orange_utils.orange_imports import gui
from ewoksorange.gui.owwidgets.threaded import OWEwoksWidgetOneThread
from silx.gui import qt

from est.core.process.write import WriteXasObject

_logger = logging.getLogger(__name__)


class XASOutputOW(OWEwoksWidgetOneThread, ewokstaskclass=WriteXasObject):
    """
    Widget used for signal extraction
    """

    name = "xas output"
    description = "Store process result (configuration)"
    icon = "icons/output.png"
    priority = 5
    keywords = ["spectroscopy", "signal", "output", "file"]

    want_main_area = True
    resizing_enabled = True
    want_control_area = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._outputWindow = qt.QWidget(parent=self)
        self._outputWindow.setLayout(qt.QGridLayout())

        self._outputWindow.layout().addWidget(qt.QLabel("file", parent=self))
        self._inputLe = qt.QLineEdit("", parent=self)
        self._outputWindow.layout().addWidget(self._inputLe, 0, 0)
        self._selectPB = qt.QPushButton("select", parent=self)
        self._outputWindow.layout().addWidget(self._selectPB, 0, 1)

        spacer = qt.QWidget(parent=self)
        spacer.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        self._outputWindow.layout().addWidget(spacer, 2, 0)

        layout = gui.vBox(self.mainArea, "output").layout()
        layout.addWidget(self._outputWindow)

        self._save = qt.QPushButton("Save")
        layout.addWidget(self._save)

        # deal with settings
        self.setFileSelected(self.get_default_input_values().get("output_file", None))

        # signal / slot connection
        self._selectPB.pressed.connect(self._selectFile)
        self._save.pressed.connect(self.handleNewSignals)

    def _selectFile(self, *args, **kwargs):
        dialog = qt.QFileDialog(self)
        dialog.setAcceptMode(qt.QFileDialog.AcceptSave)
        dialog.setFileMode(qt.QFileDialog.AnyFile)
        dialog.setNameFilters(["hdf5 files (*.hdf5, *.hdf, *.h5)"])

        if dialog.exec_() is qt.QDialog.Rejected:
            dialog.close()
            return None
        fileSelected = dialog.selectedFiles()
        if len(fileSelected) == 0:
            return None
        else:
            assert len(fileSelected) == 1
            file_ = fileSelected[0]
            if not h5py.is_hdf5(file_):
                if not file_.lower().endswith(
                    (".h5", ".hdf5", ".nx", ".nxs", ".nexus")
                ):
                    file_ += ".h5"
            self.setFileSelected(file_)
            return str(file_)

    def setFileSelected(self, file_path):
        self.update_default_inputs(output_file=file_path)
        self._inputLe.setText(file_path)

    def _getFileSelected(self):
        return self._inputLe.text()

    def _missing_file_getter(self):
        mess = qt.QMessageBox(self)
        mess.setIcon(qt.QMessageBox.Warning)
        mess.setText("No output file defined, please give a file path")
        res = mess.exec_()
        return res, self._selectFile()

    def handleNewSignals(self):
        # check if not file selected ask for one from a QDialog
        if self._getFileSelected() == "":
            res, file_path = self._missing_file_getter()
            if res:
                self.setFileSelected(file_path)
            else:
                _logger.error("task failed. No output file provided", exc_info=True)
                return
        super().handleNewSignals()
