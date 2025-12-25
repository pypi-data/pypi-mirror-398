import pytest

try:
    import larch
except ImportError:
    larch = None

from ewoks import execute_graph


@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_larch_plotspectrumdata(filename_cu_from_pymca):
    input_information = {
        "channel_url": f"spec://{filename_cu_from_pymca}?1 cu.dat 1.1 Column 2/Column 1",
        "spectra_url": f"spec://{filename_cu_from_pymca}?1 cu.dat 1.1 Column 2/Column 2",
        "energy_unit": "electron_volt",
    }

    inputs = list()
    inputs.append(
        {
            "id": "load",
            "name": "input_information",
            "value": input_information,
        }
    )
    inputs.append(
        {
            "id": "exafs",
            "name": "autobk_config",
            "value": {"clamp_lo": 1, "clamp_hi": 1},
        }
    )
    inputs.append(
        {
            "id": "ft",
            "name": "xftf_config",
            "value": {
                "kmin": 0,
                "kmax": 20,
                "kweight": 2,
                "kw": 0,
                "dk": 1,
                "window": "kaiser",
                "rmax_out": 10.0,
                "nfft": 2048,
                "kstep": 0.05,
            },
        }
    )

    inputs.append(
        {
            "id": "plotdata",
            "name": "plot_names",
            "value": (
                "mu",
                "flatten_mu",
                "normalized_mu",
                "chi_weighted_k",
                "chi",
                "ft_mag",
                "noise_savgol",
            ),
        }
    )

    result = execute_graph(_LARCH_WORKFLOW, inputs=inputs)
    assert len(result["plot_data"]) == 1

    scan_data = result["plot_data"][0]

    assert len(scan_data) == 7
    for name, data in scan_data.items():
        if name in ("chi", "chi_weighted_k"):
            n = 323
        elif name == "ft_mag":
            n = 326
        else:
            n = 1461
        assert len(data["x"]) == n
        assert len(data["y"]) == n
        assert data["xlabel"]
        assert data["ylabel"]

    assert "k^2" in scan_data["chi_weighted_k"]["ylabel"]

    if False:
        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(2, 3, figsize=(10, 10), constrained_layout=True)
        for data, ax in zip(scan_data.values(), axs.flatten()):
            ax.plot(data["x"], data["y"])
            ax.set_xlabel(data["xlabel"])
            ax.set_ylabel(data["ylabel"])
        plt.show()


_LARCH_WORKFLOW = {
    "graph": {"id": "test"},
    "nodes": [
        {
            "task_type": "class",
            "task_identifier": "est.core.process.read.ReadXasObject",
            "id": "load",
        },
        {
            "task_type": "class",
            "task_identifier": "est.core.process.larch.pre_edge.Larch_pre_edge",
            "id": "norm",
        },
        {
            "task_type": "class",
            "task_identifier": "est.core.process.larch.autobk.Larch_autobk",
            "id": "exafs",
        },
        {
            "task_type": "class",
            "task_identifier": "est.core.process.larch.xftf.Larch_xftf",
            "id": "ft",
        },
        {
            "task_type": "class",
            "task_identifier": "est.core.process.noise.NoiseProcess",
            "id": "noise",
        },
        {
            "task_type": "class",
            "task_identifier": "est.core.process.plotspectrumdata.PlotSpectrumData",
            "id": "plotdata",
        },
    ],
    "links": [
        {
            "data_mapping": [{"source_output": "xas_obj", "target_input": "xas_obj"}],
            "source": "load",
            "target": "norm",
        },
        {
            "data_mapping": [{"source_output": "xas_obj", "target_input": "xas_obj"}],
            "source": "norm",
            "target": "exafs",
        },
        {
            "data_mapping": [{"source_output": "xas_obj", "target_input": "xas_obj"}],
            "source": "exafs",
            "target": "ft",
        },
        {
            "data_mapping": [{"source_output": "xas_obj", "target_input": "xas_obj"}],
            "source": "ft",
            "target": "noise",
        },
        {
            "data_mapping": [{"source_output": "xas_obj", "target_input": "xas_obj"}],
            "source": "noise",
            "target": "plotdata",
        },
    ],
}
