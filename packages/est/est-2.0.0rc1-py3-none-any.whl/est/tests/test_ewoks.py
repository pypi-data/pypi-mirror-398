import os
import xml.etree.ElementTree as ET

import pytest

try:
    import PyMca5
except ImportError:
    PyMca5 = None

try:
    import larch
except ImportError:
    larch = None

try:
    import Orange
except ImportError:
    Orange = None


from ewokscore.graph import TaskGraph
from ewokscore.graph.analysis import start_nodes
from ewoksorange.gui.workflows.owscheme import ewoks_to_ows
from ewoksorange.gui.workflows.owscheme import ows_to_ewoks


@pytest.mark.skipif(Orange is None, reason="Orange3 is not installed")  # data converter
@pytest.mark.skipif(PyMca5 is None, reason="Pymca5 is not installed")
def test_orange_graph_pymca(example_pymca, tmpdir):
    """test conversion of a workflow based on pymca to ewoks graph
    from orange to ewoks and from ewoks to orange"""
    # step 1: from ows to ewoks graph
    graph = ows_to_ewoks(example_pymca)
    assert isinstance(graph, TaskGraph)
    assert len(start_nodes(graph.graph)) == 1
    assert len(graph.graph.edges) == 5

    # step 2: from generated ewoks graph to orange
    destination = str(tmpdir / "output_pymca_examples.ows")
    ewoks_to_ows(graph=graph, destination=destination)
    assert os.path.exists(destination)
    # ensure links and nodes are defined
    tree = ET.parse(destination)
    root = tree.getroot()
    children_tags = {elmt.tag: elmt for elmt in root}
    # test root element
    assert "nodes" in children_tags
    assert "links" in children_tags
    assert "node_properties" in children_tags

    # check links
    links = [elmt for elmt in children_tags["links"]]
    links_by_id = {link.get("id"): _get_link_info(link) for link in links}
    assert len(links_by_id) == 5


@pytest.mark.skipif(larch is None, reason="larch is not installed")
def test_orange_graph_larch(example_larch, tmpdir):
    """test conversion of a workflow based on larch to ewoks graph
    from orange to ewoks and from ewoks to orange"""
    # step 1: from ows to ewoks graph
    graph = ows_to_ewoks(example_larch)
    assert isinstance(graph, TaskGraph)
    assert len(start_nodes(graph.graph)) == 1
    assert len(graph.graph.edges) == 4

    # step 2: from generated ewoks graph to orange
    destination = str(tmpdir / "output_larch_examples.ows")
    ewoks_to_ows(graph=graph, destination=destination)
    assert os.path.exists(destination)
    # ensure links and nodes are defined
    tree = ET.parse(destination)
    root = tree.getroot()
    children_tags = {elmt.tag: elmt for elmt in root}
    # test root element
    assert "nodes" in children_tags
    assert "links" in children_tags
    assert "node_properties" in children_tags

    # check links
    links = [elmt for elmt in children_tags["links"]]
    links_by_id = {link.get("id"): _get_link_info(link) for link in links}
    assert len(links_by_id) == 4


def _get_link_info(link_node):
    return (
        link_node.get("sink_channel"),
        link_node.get("sink_node_id"),
        link_node.get("source_channel"),
        link_node.get("source_channel_id"),
    )
