"""Tools to visualize spectra"""

from silx.gui import qt
from silx.gui.plot.items.roi import RectangleROI
from silx.gui.plot.tools.roi import RegionOfInterestManager
from silx.gui.plot.tools.roi import RegionOfInterestTableWidget

from .XasObjectViewer import MapViewer


class ROISelector(qt.QWidget):
    """
    Used to defined a roi on a spectra map
    """

    sigRoiUpdated = qt.Signal()
    """signal emit when the roi is updated"""

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setLayout(qt.QVBoxLayout())
        # TODO: if data starts to be quiet large then we can load only part of
        # if. There is some code to do this on tomwer.
        self._xas_object_map = MapViewer(keys=["mu"])
        self.layout().addWidget(self._xas_object_map)
        self._plot = self._xas_object_map.getPlot()

        # Create the object controlling the ROIs and set it up
        self._roiManager = RegionOfInterestManager(self._plot)
        self._roiManager.setColor("red")  # Set the color of ROI

        self._roiManager.sigRoiAdded.connect(self.updateAddedRegionOfInterest)

        # Add a rectangular region of interest
        self._roi = RectangleROI()
        self._roi.setGeometry(origin=(0, 0), size=(2, 2))
        self._roi.setName("ROI")
        self._roiManager.addRoi(self._roi)
        self.__roi_first_definition = True
        """flag used make sure the roi is clearly visible at least during the first processing"""

        # Create the table widget displaying
        self._roiTable = RegionOfInterestTableWidget()
        self._roiTable.setRegionOfInterestManager(self._roiManager)
        self._roi.sigRegionChanged.connect(self._propagateROISig)

        # Add the region of interest table and the buttons to a dock widget
        widget = qt.QWidget()
        layout = qt.QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(self._roiTable)
        layout.addWidget(self._xas_object_map.keySelectionDocker)

        dock = qt.QDockWidget("Image ROI")
        dock.setWidget(widget)
        self._plot.addDockWidget(qt.Qt.RightDockWidgetArea, dock)

        # expose API
        self.setColormap = self._plot.setDefaultColormap

    def _propagateROISig(self, *args, **kwargs):
        self.sigRoiUpdated.emit()

    def setXasObject(self, xas_obj):
        if xas_obj is None:
            return
        self._xas_object_map.setXasObject(xas_obj=xas_obj)
        if self.__roi_first_definition is True:
            origin = (0, 0)
            size = (xas_obj.spectra.shape[1], xas_obj.spectra.shape[0])
            self.setROI(origin=origin, size=size)
            self._roi.setEditable(True)

    def getXasObject(self):
        return self._xas_object_map._xasObj

    def updateAddedRegionOfInterest(self, roi):
        """Called for each added region of interest: set the name"""
        if roi.getName() == "":
            roi.setName("ROI %d" % len(self._roiManager.getRois()))

    def setROI(self, origin, size):
        self._roi.setGeometry(origin=origin, size=size)

    def setOrigin(self, origin):
        self._roi.setOrigin(origin)

    def setSize(self, size):
        self._roi.setSize(size)

    def getROI(self):
        return self._roi


class ROISelectorDialog(qt.QDialog):
    """Dialog embedding the SoiSelector"""

    def __init__(self, parent=None):
        qt.QDialog.__init__(self, parent)
        self._mainWindow = ROISelector(parent=self)

        self.setWindowTitle("Roi selection")
        self.setWindowFlags(qt.Qt.Widget)
        types = qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel
        _buttons = qt.QDialogButtonBox(parent=self)
        _buttons.setStandardButtons(types)

        self.setLayout(qt.QVBoxLayout())
        self.layout().addWidget(self._mainWindow)
        self.layout().addWidget(_buttons)

        _buttons.accepted.connect(self.accept)
        _buttons.rejected.connect(self.reject)

    def setXasObject(self, *args, **kwargs):
        self._mainWindow.setXasObject(*args, **kwargs)

    def getXasObject(self):
        return self._mainWindow.getXasObject()

    def getROI(self):
        return self._mainWindow.getROI()

    def setROI(self, *args, **kwargs):
        self._mainWindow.setROI(*args, **kwargs)

    def setColormap(self, *args, **kwargs):
        self._mainWindow.setColormap(*args, **kwargs)


if __name__ == "__main__":
    from silx.gui.colors import Colormap

    from ..core.process.roi import _ROI
    from ..core.process.roi import ROIProcess
    from ..core.types.xasobject import XASObject
    from ..tests.data import example_spectra

    energy, spectra = example_spectra(shape=(256, 32, 64))
    xas_obj = XASObject(spectra=spectra, energy=energy, configuration=None)

    app = qt.QApplication([])

    class ROISelectorDialogTest(ROISelectorDialog):
        """Infinite update the xas obj according to ROI"""

        def accept(self):
            roi_process = ROIProcess()
            roi_ = _ROI.from_silx_def(self.getROI())
            roi_process.set_properties({"roi": roi_.to_dict()})
            update_xas_object = roi_process.process(self.getXasObject())
            self.setXasObject(update_xas_object)
            self.show()

    roiSelector = ROISelectorDialogTest()
    # keep colormap
    roiSelector.setColormap(Colormap(name="temperature", vmin=0, vmax=10))
    roiSelector.setXasObject(xas_obj=xas_obj)
    roiSelector.show()

    app.exec_()
