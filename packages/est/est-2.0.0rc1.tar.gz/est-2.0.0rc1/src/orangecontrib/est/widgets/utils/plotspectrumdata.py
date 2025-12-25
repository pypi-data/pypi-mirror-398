from ewoksorange.gui.owwidgets.nothread import OWEwoksWidgetNoThread

from est.core.process.plotspectrumdata import PlotSpectrumData


class PlotSpectrumDataOW(OWEwoksWidgetNoThread, ewokstaskclass=PlotSpectrumData):
    name = "plotdata"
    icon = "icons/plot_spectrum.png"
    # icon = NotImplemented
    description = "Gather plot data for Bliss/Flint"
    want_main_area = False

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._init_control_area()
