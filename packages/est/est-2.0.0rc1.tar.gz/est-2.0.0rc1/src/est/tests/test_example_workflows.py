"""Test the example workflows provided in the project resources"""

import pytest

try:
    import PyMca5
except ImportError:
    PyMca5 = None

try:
    import larch
except ImportError:
    larch = None


from ewoks import convert_graph
from ewoks import execute_graph
from ewoksorange.gui.workflows.owscheme import ows_to_ewoks


@pytest.fixture(params=["without_qt", "with_qt"])
def canvas(request, ewoks_orange_canvas):
    if request.param == "without_qt":
        return None
    else:
        return ewoks_orange_canvas


@pytest.mark.skipif(PyMca5 is None, reason="Pymca5 is not installed")
def test_example_pymca_exafs(example_pymca, filename_cu_from_pymca, tmpdir, canvas):
    assert_spec(
        example_pymca,
        example_pymca_inputs(example_pymca),
        filename_cu_from_pymca,
        tmpdir,
        canvas,
    )


@pytest.mark.skipif(PyMca5 is None, reason="Pymca5 is not installed")
def test_example_pymca_exafs_hdf5(
    example_pymca, hdf5_filename_cu_from_pymca, tmpdir, canvas
):
    assert_hdf5(
        example_pymca,
        example_pymca_inputs(example_pymca),
        hdf5_filename_cu_from_pymca,
        1,
        tmpdir,
        canvas,
    )


@pytest.mark.skip("normalization fails")
@pytest.mark.skipif(PyMca5 is None, reason="Pymca5 is not installed")
def test_example_pymca_fullfield(
    example_pymca, hdf5_filename_cu_from_pymca, tmpdir, canvas
):
    assert_hdf5(
        example_pymca,
        example_pymca_inputs(example_pymca),
        hdf5_filename_cu_from_pymca,
        2,
        tmpdir,
        canvas,
    )


@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_example_larch_exafs(example_larch, filename_cu_from_pymca, tmpdir, canvas):
    assert_spec(
        example_larch,
        example_larch_inputs(example_larch),
        filename_cu_from_pymca,
        tmpdir,
        canvas,
    )


@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_example_larch_exafs_hdf5(
    example_larch, hdf5_filename_cu_from_pymca, tmpdir, canvas
):
    assert_hdf5(
        example_larch,
        example_larch_inputs(example_larch),
        hdf5_filename_cu_from_pymca,
        1,
        tmpdir,
        canvas,
    )


@pytest.mark.skip("pre-edge fails")
@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_example_larch_fullfield(
    example_larch, hdf5_filename_cu_from_pymca, tmpdir, canvas
):
    assert_hdf5(
        example_larch,
        example_larch_inputs(example_larch),
        hdf5_filename_cu_from_pymca,
        2,
        tmpdir,
        canvas,
    )


@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_example_bm23_exafs(example_bm23, filename_cu_from_pymca, tmpdir, canvas):
    if canvas:
        pytest.skip("workflow waits for use input")
    assert_spec(
        example_bm23,
        example_bm23_inputs(example_bm23),
        filename_cu_from_pymca,
        tmpdir,
        canvas,
    )


@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_example_bm23_exafs_hdf5(
    example_bm23, hdf5_filename_cu_from_pymca, tmpdir, canvas
):
    if canvas:
        pytest.skip("workflow waits for use input")
    assert_hdf5(
        example_bm23,
        example_bm23_inputs(example_bm23),
        hdf5_filename_cu_from_pymca,
        1,
        tmpdir,
        canvas,
    )


@pytest.mark.skip("pre-edge fails")
@pytest.mark.skipif(larch is None, reason="xraylarch is not installed")
def test_example_bm23_fullfield(
    example_bm23, hdf5_filename_cu_from_pymca, tmpdir, canvas
):
    assert_hdf5(
        example_bm23,
        example_bm23_inputs(example_bm23),
        hdf5_filename_cu_from_pymca,
        2,
        tmpdir,
        canvas,
    )


def example_pymca_inputs(workflow):
    return list()


def example_larch_inputs(workflow):
    return list()


def example_bm23_inputs(workflow):
    return list()


def assert_spec(workflow, inputs, filename_cu_from_pymca, tmpdir, canvas):
    input_information = {
        "channel_url": f"spec://{filename_cu_from_pymca}?1 cu.dat 1.1 Column 2/Column 1",
        "spectra_url": f"spec://{filename_cu_from_pymca}?1 cu.dat 1.1 Column 2/Column 2",
        "energy_unit": "electron_volt",
    }
    return assert_execution(workflow, inputs, input_information, tmpdir, canvas)


def assert_hdf5(workflow, inputs, filename, scan, tmpdir, canvas):
    input_information = {
        "channel_url": f"silx://{filename}?/{scan}.1/measurement/energy",
        "spectra_url": f"silx://{filename}?/{scan}.1/measurement/mu",
        "energy_unit": "electron_volt",
    }
    return assert_execution(workflow, inputs, input_information, tmpdir, canvas)


def assert_execution(workflow, inputs, input_information, tmpdir, canvas):
    output_file = tmpdir / "result.h5"
    inputs.append(
        {
            "id": find_node_id(workflow, "ReadXasObject"),
            "name": "input_information",
            "value": input_information,
        }
    )
    inputs.append(
        {
            "id": find_node_id(workflow, "WriteXasObject"),
            "name": "output_file",
            "value": str(output_file),
        }
    )

    result = _execute_graph(workflow, inputs, canvas=canvas)

    output_file.exists()
    assert result["result"] == str(output_file)
    return result


def find_node_id(filename, clsname):
    adict = convert_graph(filename, None)
    for node_attrs in adict["nodes"]:
        if node_attrs["task_identifier"].endswith(clsname):
            return node_attrs["id"]


def _execute_graph(workflow, inputs, canvas=None):
    if canvas:
        canvas.load_graph(workflow, inputs=inputs)
        canvas.start_workflow()
        canvas.wait_widgets(timeout=30)
        outputs = dict(canvas.iter_output_values())
        result = outputs["output"]
    else:
        graph = ows_to_ewoks(workflow)
        result = execute_graph(
            graph, inputs=inputs, outputs=[{"all": True}], merge_outputs=True
        )
    return result
