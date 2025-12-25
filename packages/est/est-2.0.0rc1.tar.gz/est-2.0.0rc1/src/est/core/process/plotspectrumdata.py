from typing import Dict
from typing import Optional
from typing import Sequence

from ewokscore import Task


class PlotSpectrumData(
    Task,
    input_names=["xas_obj"],
    optional_input_names=["plot_names"],
    output_names=["plot_data"],
):
    def run(self):
        self.outputs.plot_data = [
            _process_plotspectrumdata(spectrum, plot_names=self.inputs.plot_names)
            for spectrum in self.inputs.xas_obj.spectra.data.flat
        ]


def _process_plotspectrumdata(
    spectrum, plot_names: Optional[Sequence] = None
) -> Dict[str, dict]:
    kweight = spectrum.larch_dict.xftf_k_weight
    plot_data = dict()
    if not plot_names:
        plot_names = ("flatten_mu", "chi_weighted_k", "ft_mag", "noise_savgol")
    for pname in plot_names:
        plot_data[pname] = _get_plotspectrumdata(spectrum, pname, kweight=kweight)
    return plot_data


def _get_plotspectrumdata(spectrum, pname, kweight: Optional[int] = None):
    ypath = _PLOTNAME_TO_YPATH.get(pname, pname)

    xpath = spectrum.get_xpath(ypath)
    x = spectrum.get_value(xpath)
    y = spectrum.get_value(ypath)

    xlabel, ylabel = spectrum.get_xy_labels(ypath, kweight=kweight)

    info = dict()
    for apath in _YPATH_TO_INFO_APATHS.get(ypath, list()):
        value = spectrum.get_value(apath)
        key = _APATH_TO_INFO_KEY.get(apath, apath)
        info[key] = value

    hlines = [
        spectrum.get_value(apath) for apath in _YPATH_TO_HLINE_APATHS.get(ypath, list())
    ]
    vlines = [
        spectrum.get_value(apath) for apath in _YPATH_TO_VLINE_APATHS.get(ypath, list())
    ]

    return {
        "name": pname,
        "x": x,
        "y": y,
        "xlabel": xlabel,
        "ylabel": ylabel,
        "info": info,
        "hlines": hlines,
        "vlines": vlines,
    }


_PLOTNAME_TO_YPATH = {
    "ft_mag": "ft.intensity",
}
_YPATH_TO_INFO_APATHS = {
    "normalized_mu": ["e0", "edge_step"],
    "flatten_mu": ["e0", "edge_step"],
    "noise_savgol": ["raw_noise_savgol", "norm_noise_savgol", "edge_step", "e0"],
}
_APATH_TO_INFO_KEY = {
    "raw_noise_savgol": "raw_noise",
    "norm_noise_savgol": "norm_noise",
}
_YPATH_TO_HLINE_APATHS = {
    "noise_savgol": ["raw_noise_savgol"],
}
_YPATH_TO_VLINE_APATHS = {
    "noise_savgol": ["noise_e_min", "noise_e_max"],
}
