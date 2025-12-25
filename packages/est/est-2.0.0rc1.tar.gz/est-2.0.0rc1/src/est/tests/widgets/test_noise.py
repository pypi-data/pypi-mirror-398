from orangecontrib.est.widgets.utils.noise import NoiseOW

from ...core.types.xasobject import XASObject
from ..widgets.utils import wait_task_executed


def test_energy_roi_widget_execute(qtapp, spectrum_cu_from_pymca):
    "Check behavior ifof the nergy roi widget"
    # create Xas obj
    energy = spectrum_cu_from_pymca.energy
    mu = spectrum_cu_from_pymca.mu
    xas_obj = XASObject(
        spectra=mu.reshape(mu.shape[0], 1, 1),
        energy=energy,
    )
    xas_obj.spectra[0, 0].edge_step = 2.8
    e0 = 100
    xas_obj.spectra[0, 0].e0 = e0
    # set edge_step otherwise will ask for pre_edge to be run first
    widget = NoiseOW()
    widget.update_default_inputs(xas_obj=xas_obj, window_size=5, polynomial_order=2)

    while qtapp.hasPendingEvents():
        qtapp.processEvents()

    # ensure xas_obj is not propagated and the widget is set up
    xas_obj = widget.get_task_output_value("xas_obj", default=None)
    assert xas_obj is None

    expected = {"window_size": 5, "polynomial_order": 2, "e_min": 150, "e_max": None}
    assert widget._window.getParameters() == expected

    # check behavior parameter changed
    widget._window._options.setEStart(220)
    wait_task_executed(qtapp, widget)
    xas_obj = widget.get_task_output_value("xas_obj", default=None)
    assert xas_obj is not None

    expected = {
        "window_size": 5,
        "polynomial_order": 2,
        "e_min": 220,
        "e_max": None,
    }
    assert widget._window.getParameters() == expected
    assert xas_obj.spectra[0, 0].noise_e_min == e0 + 220
    assert xas_obj.spectra[0, 0].noise_e_max == max(energy)
