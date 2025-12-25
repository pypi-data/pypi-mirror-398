from ewoksorange.gui.orange_utils.signals import Input
from ewoksorange.gui.orange_utils.signals import Output
from ewoksorange.gui.owwidgets.base import OWWidget
from Orange.data import Table

from est.core.types.xasobject import XASObject
from est.core.utils.converter import Converter


class IConverterOW(OWWidget):
    """
    Offer a conversion from Orange.data.Table to XASObject
    """

    name = "converter Table -> xas_obj"
    description = "convert a Orange.data.Table to a XASObject"
    icon = "icons/iconverter.png"
    priority = 6
    keywords = [
        "spectroscopy",
        "signal",
        "output",
        "file",
        "Table",
        "converter",
        "iconverter",
    ]

    want_main_area = False
    resizing_enabled = False
    want_control_area = False

    class Inputs:
        data_table = Input("Data", Table, default=True)
        # simple compatibility for some Orange widget and especially the
        # 'spectroscopy add-on'

    class Outputs:
        xas_obj = Output("xas_obj", XASObject)
        # by default we want to avoid sending 'Orange.data.Table' to avoid
        # loosing the XASObject flow process and results.

    @Inputs.data_table
    def process(self, data_table):
        if data_table is None:
            return
        xas_obj = Converter.toXASObject(data_table=data_table)
        self.Outputs.xas_obj.send(xas_obj)
