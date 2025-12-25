import logging

from ewoksorange.gui.owwidgets.meta import ow_build_opts
from ewoksorange.gui.owwidgets.threaded import OWEwoksWidgetOneThread

from est.core.types.xasobject import XASObject

_logger = logging.getLogger(__file__)


class EstProcessWidget(OWEwoksWidgetOneThread, **ow_build_opts):
    want_control_area = False

    def handleNewSignals(self):
        self.task_input_changed()
        super().handleNewSignals()

    def task_input_changed(self):
        pass

    def task_output_changed(self):
        xas_obj = self.get_task_output_value("xas_obj", default=None)
        if xas_obj is None:
            _logger.warning("no output data set. Unable to update the GUI")
            return
        if isinstance(xas_obj, dict):
            xas_obj = XASObject.from_dict(xas_obj)
        if not isinstance(xas_obj, XASObject):
            raise TypeError(str(type(xas_obj)))

        if hasattr(self, "_window") and hasattr(self._window, "setXASObj"):
            self._window.setXASObj(xas_obj=xas_obj)
        elif hasattr(self, "_window") and hasattr(self._window, "xasObjViewer"):
            if hasattr(self._window.xasObjViewer, "setXASObj"):
                self._window.xasObjViewer.setXASObj(xas_obj=xas_obj)
