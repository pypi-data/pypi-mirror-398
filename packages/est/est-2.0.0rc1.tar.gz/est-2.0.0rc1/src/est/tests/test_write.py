import pytest

from ..core.types.xasobject import XASObject

# from silx.io.utils import h5py_read_dataset
# import h5py

try:
    import larch
except ImportError:
    larch = None
else:
    from ..core.process.larch.pre_edge import Larch_pre_edge


@pytest.mark.skipif(larch is None, reason="larch is not installed")
def test_write(spectrum_cu_from_larch, tmpdir):
    xas_obj = XASObject(
        spectra=(spectrum_cu_from_larch,), energy=spectrum_cu_from_larch.energy
    )

    assert spectrum_cu_from_larch.pre_edge is None
    assert spectrum_cu_from_larch.e0 is None
    process = Larch_pre_edge(inputs={"xas_obj": xas_obj, "pre_edge_config": {}})
    process.run()
    assert spectrum_cu_from_larch.pre_edge is not None
    assert spectrum_cu_from_larch.e0 is not None

    # check process
    # output_file = tmpdir / "output.h5"
    # xas_obj.to_file(str(output_file))
    # assert output_file.exists()
    # with h5py.File(str(output_file), "r") as h5f:
    #     scan = h5f["scan1"]
    # pre_edge_process = scan["xas_process_1"]
    # # check general informqtion
    # assert "class_instance" in pre_edge_process
    # assert "date" in pre_edge_process
    # assert "processing_order" in pre_edge_process
    # assert "program" in pre_edge_process
    # assert "version" in pre_edge_process
    # assert h5py_read_dataset(pre_edge_process["program"]) == "larch_pre_edge"

    # # check results
    # assert "results" in pre_edge_process
    # results_grp = pre_edge_process["results"]
    # assert "mu" in results_grp
    # assert "normalized_mu" in results_grp
