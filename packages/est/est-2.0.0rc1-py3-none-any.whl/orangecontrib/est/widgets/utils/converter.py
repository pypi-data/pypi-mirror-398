from ewoksorange.gui.orange_utils.signals import Input
from ewoksorange.gui.orange_utils.signals import Output
from ewoksorange.gui.owwidgets.base import OWWidget
from Orange.data import Table

from est.core.types.xasobject import XASObject
from est.core.utils.converter import Converter


class ConverterOW(OWWidget):
    """
    Offer a conversion from XASObject to Orange.data.Table, commonly used
    from Orange widget
    """

    name = "converter xas_obj -> Table"
    description = "convert a XASObject to a Orange.data.Table"
    icon = "icons/converter.png"
    priority = 5
    keywords = ["spectroscopy", "signal", "output", "file"]

    want_main_area = False
    want_control_area = False
    resizing_enabled = False

    class Inputs:
        xas_obj = Input("xas_obj", XASObject, default=True)
        # simple compatibility for some Orange widget and especialy the
        # 'spectroscopy add-on'

    class Outputs:
        res_data_table = Output("Data", Table)
        # by default we want to avoid sending 'Orange.data.Table' to avoid
        # loosing the XASObject flow process and results.

    @Inputs.xas_obj
    def process(self, xas_object):
        if xas_object is None:
            return
        data_table = Converter.toDataTable(xas_object=xas_object)
        self.Outputs.res_data_table.send(data_table)
