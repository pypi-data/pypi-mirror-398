import os

import pytest
import testbook

try:
    import PyMca5
except ImportError:
    PyMca5 = None

root_dir = os.path.join(os.path.dirname(__file__), "notebooks")


@pytest.mark.skipif(PyMca5 is None, reason="PyMca5 is not installed")
def test_notebook_pymca_xas_process():
    filename = os.path.join(root_dir, "pymca_xas_process.ipynb")
    with testbook.testbook(filename, execute=True):
        pass
