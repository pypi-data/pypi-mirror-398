from orangecontrib.est.widgets.utils.energyroi import EnergyRoiOW

from ...core.types.xasobject import XASObject
from ..widgets.utils import wait_task_executed


def test_energy_roi_widget_behavior(qtapp, spectrum_cu_from_pymca):
    "Check behavior ifof the nergy roi widget"
    # create Xas obj
    energy = spectrum_cu_from_pymca.energy
    mu = spectrum_cu_from_pymca.mu
    xas_obj = XASObject(
        spectra=mu.reshape(mu.shape[0], 1, 1),
        energy=energy,
    )

    new_energy_roi = (8700, 9500)
    assert energy.min() < new_energy_roi[0]
    assert energy.max() > new_energy_roi[1]

    widget = EnergyRoiOW()
    widget.update_default_inputs(xas_obj=xas_obj)
    widget.task_input_changed()
    widget.loadSettings(
        energy_roi={"minE": new_energy_roi[0], "maxE": new_energy_roi[1]}
    )
    while qtapp.hasPendingEvents():
        qtapp.processEvents()

    # ensure xas_obj is not propagated and the widget is set up
    xas_obj = widget.get_task_output_value("xas_obj", default=None)
    assert xas_obj is None
    assert widget._widget.getXasObject() is not None
    assert widget._widget.getROI() == new_energy_roi

    # check behavior once validated
    widget.validate()
    wait_task_executed(qtapp, widget)
    xas_obj = widget.get_task_output_value("xas_obj", default=None)
    assert xas_obj is not None
    assert xas_obj.energy.min() >= new_energy_roi[0]
    assert xas_obj.energy.max() <= new_energy_roi[1]
