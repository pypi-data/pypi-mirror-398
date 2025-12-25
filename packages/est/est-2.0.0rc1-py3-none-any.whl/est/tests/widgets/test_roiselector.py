import numpy

from orangecontrib.est.widgets.utils.roi import RoiSelectionOW

from ...core.types.xasobject import XASObject
from ..widgets.utils import wait_task_executed


def test_roi_selection_widget(qtapp, spectrum_cu_from_pymca):
    """
    Check behavior if we provide to the widget some valid inputs
    """
    energy = spectrum_cu_from_pymca.energy
    mu = spectrum_cu_from_pymca.mu
    spectra = numpy.concatenate([mu] * 100).reshape(mu.shape[0], 10, 10)
    xas_obj = XASObject(
        spectra=spectra,
        energy=energy,
    )

    roi_origin = (5, 5)
    roi_size = (2, 2)
    widget = RoiSelectionOW()
    widget.update_default_inputs(
        xas_obj=xas_obj,
    )
    widget.task_input_changed()

    widget.loadSettings(
        roi_origin=roi_origin,
        roi_size=roi_size,
    )
    while qtapp.hasPendingEvents():
        qtapp.processEvents()
    assert tuple(widget.getROIOrigin()) == roi_origin
    assert tuple(widget.getROISize()) == roi_size

    widget.validate()
    wait_task_executed(qtapp, widget)
    xas_obj = widget.get_task_output_value("xas_obj", default=None)
    assert xas_obj is not None
    assert xas_obj.n_spectrum == roi_size[0] * roi_size[1]
